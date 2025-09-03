import { clsx } from "clsx";

export default function TierBadge({ tier }: { tier?: string | null }) {
  const t = (tier || "anonymous").toLowerCase();
  const color =
    t === "admin" ? "bg-rose-600" :
    t === "elevated" ? "bg-indigo-600" :
    "bg-zinc-600";

  const label =
    t === "admin" ? "admin" :
    t === "elevated" ? "elevated" :
    "anonymous";

  return (
    <span className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] bg-white/70 dark:bg-zinc-900/60 shadow-sm">
      <span className={clsx("h-2 w-2 rounded-full", color)} />
      {label}
    </span>
  );
}
