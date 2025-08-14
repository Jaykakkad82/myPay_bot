import { useEffect, useState } from "react";
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
  const { sessionId, messages, busy, error, send, clear, scrollRef } = useChat();
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    health().then((h) => setOk(!!h.ok)).catch(() => setOk(false));
  }, []);

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-sky-50 via-white to-indigo-50 dark:from-zinc-900 dark:via-zinc-950 dark:to-black text-zinc-900 dark:text-zinc-100">
      {/* Centered container */}
      
      <div className="mx-auto max-w-3xl px-3 sm:px-6 py-8">
        {/* Header */}
        <header className="mb-5 flex items-center justify-between">
          <h1 className="text-3xl font-semibold tracking-tight">
            myPayments <span className="opacity-60">•</span> <span className="text-indigo-600 dark:text-indigo-300">Agent Chat</span>
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
            {messages.map((m) => <MessageBubble key={m.id} m={m} />)}
            {busy && (
              <div className="text-xs opacity-70">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-indigo-500 mr-2" />
                thinking…
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="h-px bg-zinc-200/80 dark:bg-zinc-800/80" />

          {/* Input */}
          <div className="p-3 sm:p-4">
            {error && <div className="text-xs text-rose-600 mb-2">{error}</div>}
            <ChatInput disabled={busy} onSend={send} />
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
