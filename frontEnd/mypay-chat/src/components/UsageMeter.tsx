type Meter = { used?: number; max?: number };
type Limits = {
  requests?: Meter;
  tools?: Meter;
  tokens?: Meter;
};

function Chip({ label, used, max }: { label: string; used?: number; max?: number }) {
  const text =
    typeof used === "number" && typeof max === "number"
      ? `${used}/${max}`
      : typeof used === "number"
      ? `${used}`
      : "—";

  return (
    <span className="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] bg-white/70 dark:bg-zinc-900/60 shadow-sm">
      <span className="font-medium">{label}</span>
      <span className="opacity-70">{text}</span>
    </span>
  );
}

export default function UsageMeter({ limits }: { limits?: Limits | null }) {
  const r = limits?.requests;
  const t = limits?.tools;
  const k = limits?.tokens;
  return (
    <div className="flex items-center gap-2">
      <Chip label="req" used={r?.used} max={r?.max} />
      <Chip label="tools" used={t?.used} max={t?.max} />
      <Chip label="tok" used={k?.used} max={k?.max} />
    </div>
  );
}
