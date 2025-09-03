import { useEffect, useMemo, useRef, useState } from "react";
import { v4 as uuid } from "uuid";
import {
  sendChat,
  approve as apiApprove,
  deny as apiDeny,
  startSession,
  getSessionId,
  setSessionId,
  clearSessionId,
  ApiError,
  type AssistantMessage,
  type TraceStep,
  type ToolCall,
} from "../lib/api";

export type Role = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: Role;
  content: string;
  ts: number | string;
  trace?: TraceStep[];
  tool_calls?: ToolCall[];
  pending_approval?: AssistantMessage["pending_approval"];
  notifications?: any;
}

export interface ChatOptions {
  initialSessionId?: string; // kept for compatibility with your UI
  defaultCustomerId?: number;
}

export function useChat(opts?: ChatOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Store the latest resume blob from backend for approval resume
  const lastStateRef = useRef<any>(null);

  // ---- Server session management ----
  const [sessionId, setSessionIdState] = useState<string | null>(null);
  const [bootstrapping, setBootstrapping] = useState<boolean>(true);

  // Ensure a server session exists (create if missing)
  async function ensureSession(): Promise<string> {
    let sid = getSessionId();
    if (!sid && opts?.initialSessionId) {
      // allow an externally provided id (rare)
      console.log("Using externally provided session ID:", opts.initialSessionId);
      sid = opts.initialSessionId;
      setSessionId(sid);
    }
    if (!sid) {
      console.log("No session, starting a new one...");
      const s = await startSession();
      console.log("New session started:", s.sessionId);
      sid = s.sessionId;
    }
    setSessionIdState(sid);
    return sid;
  }

  useEffect(() => {
    (async () => {
      try {
        await ensureSession();
      } catch (e: any) {
        setError(e?.message || "Failed to start session.");
      } finally {
        setBootstrapping(false);
      }
    })();
  }, [opts?.initialSessionId]);

  // Keep scroll pinned to bottom on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 1e9, behavior: "smooth" });
  }, [messages.length]);

  const sessionReady = !!(sessionId || getSessionId()) && !bootstrapping;


  // ---- Chat send with one-time 401 retry ----
  async function send(
    text: string,
    extras?: { customerId?: number; from?: string; to?: string; currency?: string }
  ) {
    if (!text.trim() || busy) return;
    setError(null);

    const userMsg: Message = {
      id: uuid(),
      role: "user",
      content: text,
      ts: Date.now(),
    };
    setMessages((m) => [...m, userMsg]);
    setBusy(true);

    const doSend = async () =>
      await sendChat(text, {
        customerId: extras?.customerId,
        from: extras?.from,
        to: extras?.to,
        currency: extras?.currency,
      });

    try {
      // make sure session exists
      if (!sessionId) await ensureSession();

      let res: AssistantMessage;
      try {
        res = await doSend();
      } catch (err: any) {
        if (err instanceof ApiError && err.status === 401) {
          // bootstrap a new session & retry once
          await startSession();
          setSessionIdState(getSessionId());
          res = await doSend();
        } else {
          throw err;
        }
      }

      // keep resume blob
      lastStateRef.current = res.resume ?? null;

      const botMsg: Message = {
        id: res.id || uuid(),
        role: "assistant",
        content: res.content,
        ts: res.ts || Date.now(),
        trace: res.trace || [],
        tool_calls: res.tool_calls || [],
        pending_approval: res.pending_approval || null,
      };
      setMessages((m) => [...m, botMsg]);
    } catch (e: any) {
      setError(e?.message || "Something went wrong");
      const errMsg: Message = {
        id: uuid(),
        role: "assistant",
        content:
          "Sorry, I hit an error while processing that. Please try again in a moment.",
        ts: Date.now(),
      };
      setMessages((m) => [...m, errMsg]);
    } finally {
      setBusy(false);
    }
  }

  // ---- Approve/deny with 401 retry ----
  async function approvePending(approvalId: string) {
    if (!approvalId || !lastStateRef.current) {
      setError("Nothing to approve.");
      return;
    }
    setBusy(true);
    try {
      const tryApprove = () => apiApprove(approvalId, lastStateRef.current);
      let res: AssistantMessage;
      try {
        res = await tryApprove();
      } catch (err: any) {
        if (err instanceof ApiError && err.status === 401) {
          await startSession();
          setSessionIdState(getSessionId());
          res = await tryApprove();
        } else {
          throw err;
        }
      }
      lastStateRef.current = res.resume ?? lastStateRef.current;

      const botMsg: Message = {
        id: res.id || uuid(),
        role: "assistant",
        content: res.content,
        ts: res.ts || Date.now(),
        trace: res.trace || [],
        tool_calls: res.tool_calls || [],
        pending_approval: res.pending_approval || null,
      };
      setMessages((m) => [...m, botMsg]);
    } catch (e: any) {
      setError(e?.message || "Approval failed");
    } finally {
      setBusy(false);
    }
  }

  async function denyPending(approvalId: string) {
    if (!approvalId || !lastStateRef.current) {
      setError("Nothing to reject.");
      return;
    }
    setBusy(true);
    try {
      const tryDeny = () => apiDeny(approvalId, lastStateRef.current);
      let res: AssistantMessage;
      try {
        res = await tryDeny();
      } catch (err: any) {
        if (err instanceof ApiError && err.status === 401) {
          await startSession();
          setSessionIdState(getSessionId());
          res = await tryDeny();
        } else {
          throw err;
        }
      }

      const botMsg: Message = {
        id: res.id || uuid(),
        role: "assistant",
        content: res.content,
        ts: res.ts || Date.now(),
        trace: res.trace || [],
        tool_calls: res.tool_calls || [],
        pending_approval: res.pending_approval || null,
      };
      setMessages((m) => [...m, botMsg]);
    } catch (e: any) {
      setError(e?.message || "Reject failed");
    } finally {
      setBusy(false);
    }
  }

  function clear() {
    setMessages([]);
    lastStateRef.current = null;
  }

  return {
    sessionId: sessionId || getSessionId() || "",
    sessionReady,
    messages,
    busy: busy || bootstrapping,
    error,
    send,
    clear,
    scrollRef,
    approvePending,
    denyPending,
    lastStateRef,
  };
}
