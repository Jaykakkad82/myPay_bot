import { useState } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (accessKey: string) => Promise<boolean> | boolean;
  loading?: boolean;
  error?: string | null;
};

export default function UpgradeModal({ open, onClose, onSubmit, loading, error }: Props) {
  const [key, setKey] = useState("");

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-sm rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-xl p-4">
        <div className="text-sm font-medium mb-2">Enter access key</div>
        <input
          type="text"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="ACCESS-XXXX-YYYY"
          className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
        />
        {error && <div className="text-xs text-rose-600 mt-2">{error}</div>}
        <div className="mt-3 flex justify-end gap-2">
          <button
            className="px-3 py-1.5 rounded-lg text-sm border hover:bg-zinc-50 dark:hover:bg-zinc-800"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            className="px-3 py-1.5 rounded-lg text-sm bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60"
            onClick={async () => {
              const ok = await onSubmit(key.trim());
              if (ok) onClose();
            }}
            disabled={loading || !key.trim()}
          >
            {loading ? "Upgrading…" : "Upgrade"}
          </button>
        </div>
      </div>
    </div>
  );
}
