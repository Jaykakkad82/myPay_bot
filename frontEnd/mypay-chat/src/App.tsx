import { useEffect, useMemo, useState } from "react";
import ChatInput from "./components/ChatInput";
import MessageBubble from "./components/MessageBubble";
import { useChat } from "./hooks/useChat";
import { health } from "./lib/api";
import TierBadge from "./components/TierBadge";
import UsageMeter from "./components/UsageMeter";
import UpgradeModal from "./components/UpgradeModal";
import LimitBanner from "./components/LimitBanner";
import Footer from "./components/footer";
import { useLimits } from "./hooks/useLimits";

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


// Try to parse `{...}` JSON at end of "429 … – {...}"
function parseLimitFromError(msg?: string): { reason?: string; retryAfterSec?: number } | null {
  if (!msg) return null;
  if (!/^429\b/.test(msg)) return null;
  const idx = msg.indexOf("–");
  if (idx >= 0) {
    const maybe = msg.slice(idx + 1).trim();
    try {
      const obj = JSON.parse(maybe);
      const reason = obj?.reason || obj?.detail || obj?.message;
      const retryAfterSec = obj?.retryAfterSec ?? obj?.retry_after ?? obj?.retryAfter ?? undefined;
      return { reason, retryAfterSec };
    } catch {
      // ignore
    }
  }
  return { reason: msg, retryAfterSec: undefined };
}

export default function App() {
  const { sessionId,  sessionReady,  messages, busy, error, send, clear, scrollRef, approvePending, denyPending } = useChat();
  const { tier, limits, loading: limitsLoading, error: limitsError, refresh, upgrade, upgrading, upgradeError, setUpgradeError } = useLimits({ enabled: sessionReady });

  const [ok, setOk] = useState<boolean | null>(null);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [limitBanner, setLimitBanner] = useState<{ reason?: string; retryAfterSec?: number } | null>(null);

  // Frontend-only latency (per assistant turn)
  const [sendStartedAt, setSendStartedAt] = useState<number | null>(null);
  const [lastLatencyMs, setLastLatencyMs] = useState<number | null>(null);

  const sendWithLatency = (
    text: string,
    extras?: { customerId?: number; from?: string; to?: string; currency?: string }
  ) => {
    setSendStartedAt(performance.now());
    setLastLatencyMs(null);
    setLimitBanner(null); // clear banner on new try
    send(text, extras);
  };

  useEffect(() => {
    if (!busy && sendStartedAt != null && messages.length > 0) {
      const last = messages[messages.length - 1];
      if (last.role === "assistant") {
        const ms = Math.max(0, Math.round(performance.now() - sendStartedAt));
        setLastLatencyMs(ms);
        setSendStartedAt(null);
        // refresh limits after each answer
        refresh();
      }
    }
  }, [busy, messages, sendStartedAt, refresh]);

  useEffect(() => {
    health().then((h) => setOk(!!h.ok)).catch(() => setOk(false));
  }, []);

  // Parse 429 into a friendly banner
  useEffect(() => {
    const parsed = parseLimitFromError(error || undefined);
    if (parsed) setLimitBanner(parsed);
  }, [error]);

  useEffect(() => {
    if (sessionId) {
      refresh();
    }
  }, [sessionId, refresh]);

  useEffect(() => {
    if (tier) setLimitBanner(null);
  }, [tier]);

  const latencyLabel = useMemo(() => {
    if (lastLatencyMs == null) return null;
    if (lastLatencyMs < 1000) return `${lastLatencyMs} ms`;
    const s = (lastLatencyMs / 1000).toFixed(1);
    return `${s}s`;
  }, [lastLatencyMs]);

  const handleUpgradeSubmit = async (accessKey: string): Promise<boolean> => {
  try {
    // await upgrade(accessKey);          // your existing hook fn
    // setShowUpgrade(false);             // close on success
    // return true;                       // matches expected type
    const ok = await upgrade(accessKey); // returns boolean
      if (ok) {
            setLimitBanner(null);
            await refresh();
            setShowUpgrade(false);
          }
          return ok;
        }
  catch (e) { return false}
};


  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-sky-50 via-white to-indigo-50 dark:from-zinc-900 dark:via-zinc-950 dark:to-black text-zinc-900 dark:text-zinc-100">
      <main className="flex-1">
      <div className="mx-auto max-w-3xl px-3 sm:px-6 py-8">
        {/* Header */}
        <header className="mb-5 flex items-center justify-between">
          <h1 className="text-3xl font-semibold tracking-tight">
            myPayments <span className="opacity-60">•</span>{" "}
            <span className="text-indigo-600 dark:text-indigo-300">Agent Chat</span>
          </h1>

          <div className="flex items-center gap-2">
            {/* Session badge + copy */}
            <span className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] bg-white/70 dark:bg-zinc-900/60 shadow-sm">
              <span className="font-mono">{sessionId?.slice(0, 8) || "…"}</span>
              <button
                onClick={() => navigator.clipboard.writeText(sessionId || "")}
                className="opacity-70 hover:opacity-100 underline decoration-dotted"
                title="Copy session id"
              >
                copy
              </button>
            </span>

            <TierBadge tier={tier} />
            <UsageMeter limits={limits || undefined} />

            <button
              className="text-[11px] px-3 py-1 rounded-full border hover:bg-zinc-50 dark:hover:bg-zinc-800"
              onClick={() => { setUpgradeError(null); setShowUpgrade(true); }}
            >
              Enter access key
            </button>

            <StatusPill ok={ok} />
          </div>
        </header>

        {/* Limits errors */}
        {limitsError && (
          <div className="mb-3 text-xs text-amber-700 bg-amber-50 dark:bg-amber-900/30 border border-amber-300/60 dark:border-amber-900/40 rounded-xl p-2">
            {limitsError}
          </div>
        )}

        {/* 429 banner */}
        {limitBanner && (
          <LimitBanner
            reason={limitBanner.reason}
            retryAfterSec={limitBanner.retryAfterSec}
            onClose={() => setLimitBanner(null)}
            onUpgradeClick={() => { setUpgradeError(null); setShowUpgrade(true); }}
          />
        )}

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

          {/* Divider */}
          <div className="h-px bg-zinc-200/80 dark:bg-zinc-800/80 shadow-[0_-6px_12px_-8px_rgba(0,0,0,0.12)] dark:shadow-[0_-6px_12px_-8px_rgba(0,0,0,0.5)]" />

          {/* Input */}
          <div className="p-3 sm:p-4 bg-gradient-to-t from-white/95 via-white/75 to-transparent dark:from-zinc-900/95 dark:via-zinc-900/60 rounded-b-3xl">
            {/* keep generic errors here too (non-429) */}
            {error && !/^429\b/.test(error) && (
              <div className="text-xs text-rose-600 mb-2">{error}</div>
            )}
            <ChatInput disabled={busy} onSend={sendWithLatency} />
            <div className="mt-2 flex items-center justify-between text-[11px] opacity-70">
              <button onClick={clear} className="hover:opacity-100">Clear</button>
              <span>{limitsLoading ? "loading limits…" : "Tip: use YYYY-MM-DD; dates are normalized to full ISO."}</span>
            </div>
          </div>
        </div>
      </div>
      </main>

      <Footer />

      {/* Upgrade modal */}
      <UpgradeModal
        open={showUpgrade}
        onClose={() => setShowUpgrade(false)}
        onSubmit={handleUpgradeSubmit}
        loading={upgrading}
        error={upgradeError}
      />
    </div>
  );
}
