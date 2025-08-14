import { useEffect, useMemo, useRef, useState } from "react";
import { v4 as uuid } from "uuid";
import { sendChat, type ChatResponse } from "../lib/api";

export type Role = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: Role;
  content: string;
  ts: number;
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

  const sessionId = useMemo(() => {
    const fromStore =
      opts?.initialSessionId || localStorage.getItem("mp_session_id");
    if (fromStore) return fromStore;
    const sid = uuid();
    localStorage.setItem("mp_session_id", sid);
    return sid;
  }, [opts?.initialSessionId]);

  useEffect(() => {
    // autoscroll on new message
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
      const payload = {
        sessionId,
        message: text,
        ...(extras?.customerId ? { customerId: extras.customerId } : {}),
        ...(extras?.from ? { from: extras.from } : {}),
        ...(extras?.to ? { to: extras.to } : {}),
        ...(extras?.currency ? { currency: extras.currency } : {}),
      };
      const res: ChatResponse = await sendChat(payload);
      const botMsg: Message = {
        id: uuid(),
        role: "assistant",
        content: res.answer,
        ts: Date.now(),
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

  function clear() {
    setMessages([]);
  }

  return { sessionId, messages, busy, error, send, clear, scrollRef };
}
