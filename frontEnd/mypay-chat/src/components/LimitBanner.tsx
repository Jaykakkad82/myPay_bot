import { useEffect, useState } from "react";

type Props = {
  reason?: string;
  retryAfterSec?: number;
  onClose?: () => void;
  onUpgradeClick?: () => void;
};

export default function LimitBanner({ reason, retryAfterSec, onClose, onUpgradeClick }: Props) {
  const [left, setLeft] = useState<number | undefined>(retryAfterSec);

  useEffect(() => {
    if (retryAfterSec == null) return;
    setLeft(retryAfterSec);
    const id = setInterval(() => {
      setLeft((s) => (typeof s === "number" ? Math.max(0, s - 1) : s));
    }, 1000);
    return () => clearInterval(id);
  }, [retryAfterSec]);

  return (
    <div className="mb-3 rounded-xl border border-amber-300/60 bg-amber-50 dark:bg-amber-900/30 dark:border-amber-900/40 p-3 text-xs flex items-start justify-between gap-3">
      <div>
        <div className="font-medium mb-0.5">Rate limit reached</div>
        <div className="opacity-80">
          {reason || "Please wait before trying again."}
          {typeof left === "number" && (
            <> — retry in <span className="font-mono">{left}s</span></>
          )}
        </div>
        <div className="mt-2 flex gap-2">
          <button
            className="px-2 py-1 rounded bg-indigo-600 text-white"
            onClick={onUpgradeClick}
          >
            Enter access key
          </button>
          <button
            className="px-2 py-1 rounded border"
            onClick={onClose}
          >
            Hide
          </button>
        </div>
      </div>
      <span className="text-lg">⚠️</span>
    </div>
  );
}
