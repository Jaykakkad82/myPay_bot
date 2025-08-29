import { useEffect, useMemo, useState } from "react";
import ChatInput from "./components/ChatInput";
import MessageBubble from "./components/MessageBubble";
import { useChat } from "./hooks/useChat";
import { health } from "./lib/api";

function StatusPill({ ok }: { ok: boolean | null }) {
  const label = ok === null ? "checking…" : ok ? "online" : "offline";
  const color = ok === null ? "bg-zinc-400" : ok ? "bg-emerald-500" : "bg-rose-500";
  return (
    <span className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs bg-white/70 dark:bg-zinc-900/60 shadow-sm">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      backend: {label}
    </span>
  );
}

export default function App() {
  const { sessionId, messages, busy, error, send, clear, scrollRef, approvePending, denyPending } = useChat();
  const [ok, setOk] = useState<boolean | null>(null);

  // Frontend-only latency (per assistant turn)
  const [sendStartedAt, setSendStartedAt] = useState<number | null>(null);
  const [lastLatencyMs, setLastLatencyMs] = useState<number | null>(null);

  // Wrap send: record start timestamp locally
  const sendWithLatency = (text: string, extras?: { customerId?: number; from?: string; to?: string; currency?: string }) => {
    setSendStartedAt(performance.now());
    setLastLatencyMs(null);
    send(text, extras);
  };

  // When the backend response lands (busy -> false and last message is assistant),
  // compute the turn latency on the frontend only.
  useEffect(() => {
    if (!busy && sendStartedAt != null && messages.length > 0) {
      const last = messages[messages.length - 1];
      if (last.role === "assistant") {
        const ms = Math.max(0, Math.round(performance.now() - sendStartedAt));
        setLastLatencyMs(ms);
        setSendStartedAt(null);
      }
    }
  }, [busy, messages, sendStartedAt]);

  useEffect(() => {
    health().then((h) => setOk(!!h.ok)).catch(() => setOk(false));
  }, []);

  // Small helper: format latency nicely
  const latencyLabel = useMemo(() => {
    if (lastLatencyMs == null) return null;
    if (lastLatencyMs < 1000) return `${lastLatencyMs} ms`;
    const s = (lastLatencyMs / 1000).toFixed(1);
    return `${s}s`;
  }, [lastLatencyMs]);

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-sky-50 via-white to-indigo-50 dark:from-zinc-900 dark:via-zinc-950 dark:to-black text-zinc-900 dark:text-zinc-100">
      {/* Centered container */}
      <div className="mx-auto max-w-3xl px-3 sm:px-6 py-8">
        {/* Header */}
        <header className="mb-5 flex items-center justify-between">
          <h1 className="text-3xl font-semibold tracking-tight">
            myPayments <span className="opacity-60">•</span>{" "}
            <span className="text-indigo-600 dark:text-indigo-300">Agent Chat</span>
          </h1>
          <StatusPill ok={ok} />
        </header>

        <p className="text-xs opacity-70 mb-3">
          Session: <span className="font-mono">{sessionId}</span>
        </p>

        {/* Card */}
        <div className="rounded-3xl border border-zinc-200/60 dark:border-zinc-800/60 bg-white/80 dark:bg-zinc-900/70 shadow-xl backdrop-blur">
          {/* Messages */}
          <div
            ref={scrollRef}
            className="h-[65vh] overflow-y-auto p-4 sm:p-6 flex flex-col gap-4"
          >
            {messages.length === 0 && (
              <div className="opacity-70 text-sm leading-6">
                Try:
                <ul className="list-disc ml-6 mt-1 space-y-1">
                  <li>“Show spend for customer 1 from 2023-09-01 to 2023-09-30 in USD.”</li>
                  <li>“Breakdown by category for that window.”</li>
                  <li>“Search transactions for customer 1, status COMPLETED.”</li>
                </ul>
              </div>
            )}

            {messages.map((m, i) => {
              const isLastAssistant = i === messages.length - 1 && m.role === "assistant";
              return (
                <div key={m.id} className="flex flex-col gap-1">
                  <MessageBubble
                    m={m}
                    onApprove={approvePending}
                    onDeny={denyPending}
                  />
                  {isLastAssistant && latencyLabel && (
                    <div className="pl-12 text-[10px] text-zinc-500 dark:text-zinc-400">
                      answered in {latencyLabel}
                    </div>
                  )}
                </div>
              );
            })}

            {busy && (
              <div className="text-xs opacity-70">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-indigo-500 mr-2" />
                thinking…
              </div>
            )}
          </div>

          {/* Divider with soft shadow */}
          <div className="h-px bg-zinc-200/80 dark:bg-zinc-800/80 shadow-[0_-6px_12px_-8px_rgba(0,0,0,0.12)] dark:shadow-[0_-6px_12px_-8px_rgba(0,0,0,0.5)]" />

          {/* Input (subtle sticky feel + gradient top) */}
          <div className="p-3 sm:p-4 bg-gradient-to-t from-white/95 via-white/75 to-transparent dark:from-zinc-900/95 dark:via-zinc-900/60 rounded-b-3xl">
            {error && <div className="text-xs text-rose-600 mb-2">{error}</div>}
            <ChatInput disabled={busy} onSend={sendWithLatency} />
            <div className="mt-2 flex items-center justify-between text-[11px] opacity-70">
              <button onClick={clear} className="hover:opacity-100">Clear</button>
              <span>Tip: use YYYY-MM-DD; dates are normalized to full ISO.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
