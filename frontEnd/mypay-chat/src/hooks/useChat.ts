import { useEffect, useMemo, useRef, useState } from "react";
import { v4 as uuid } from "uuid";
import {
  sendChat,
  approve as apiApprove,
  deny as apiDeny,
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
  initialSessionId?: string;
  defaultCustomerId?: number;
}

export function useChat(opts?: ChatOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Store the latest resume blob from backend for approval resume
  const lastStateRef = useRef<any>(null);

  const sessionId = useMemo(() => {
    const fromStore =
      opts?.initialSessionId || localStorage.getItem("mp_session_id");
    if (fromStore) return fromStore;
    const sid = uuid();
    localStorage.setItem("mp_session_id", sid);
    return sid;
  }, [opts?.initialSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 1e9, behavior: "smooth" });
  }, [messages.length]);

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

    try {
      const res: AssistantMessage = await sendChat(text, {
        customerId: extras?.customerId,
        from: extras?.from,
        to: extras?.to,
        currency: extras?.currency,
      });

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

  // Approve/deny helpers (use lastStateRef)
  async function approvePending(approvalId: string) {
    if (!approvalId || !lastStateRef.current) {
      setError("Nothing to approve.");
      return;
    }
    setBusy(true);
    try {
      const res = await apiApprove(approvalId, lastStateRef.current);
      // update resume for possible chained approvals
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
      const res = await apiDeny(approvalId, lastStateRef.current);
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
    sessionId,
    messages,
    busy,
    error,
    send,
    clear,
    scrollRef,
    // expose approval actions + state for consumers
    approvePending,
    denyPending,
    lastStateRef,
  };
}
