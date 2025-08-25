import type { TraceStep } from "../lib/api";

const statusStyle: Record<string, string> = {
  ok: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  start: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200",
  skipped: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-200",
  pending_approval: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  needs_approval: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  error: "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200",
};

export default function TraceChips({ trace }: { trace: TraceStep[] }) {
  if (!trace?.length) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {trace.map((t, i) => (
        <span
          key={i}
          title={t.details ? JSON.stringify(t.details, null, 2) : undefined}
          className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-[11px] border
            ${statusStyle[t.status] ?? "bg-zinc-100 text-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-200"}
            border-zinc-200/60 dark:border-zinc-700/60`}
        >
          <span className="font-medium">{t.node}</span>
          <span className="opacity-60">·</span>
          <span>{t.status}</span>
        </span>
      ))}
    </div>
  );
}
