import { useState } from "react";
import type { ToolCall } from "../lib/api";

export default function ToolCalls({ calls }: { calls: ToolCall[] }) {
  const [open, setOpen] = useState(false);
  if (!calls?.length) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="text-xs underline decoration-dotted opacity-80 hover:opacity-100"
      >
        {open ? "Hide" : "Show"} tool calls ({calls.length})
      </button>
      {open && (
        <div className="mt-2 space-y-2">
          {calls.map((c, idx) => (
            <div
              key={idx}
              className="rounded-lg border border-zinc-200/60 dark:border-zinc-700/60 bg-white/70 dark:bg-zinc-900/60 p-2"
            >
              <div className="text-xs font-semibold">
                <span className="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-200">
                  {c.tool}
                </span>
              </div>
              <pre className="mt-1 text-[11px] leading-5 overflow-x-auto">
                {JSON.stringify(c.args, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
