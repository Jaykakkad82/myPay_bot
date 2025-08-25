import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { format } from "date-fns";
import { clsx } from "clsx";
import type { Message } from "../hooks/useChat";
import TraceChips from "./TraceChips";
import ToolCalls from "./ToolCalls";

function Avatar({ role }: { role: "user" | "assistant" | "system" }) {
  const isUser = role === "user";
  const bg = isUser ? "bg-indigo-600" : "bg-emerald-600";
  const label = isUser ? "U" : "A";
  return (
    <div className={`h-8 w-8 rounded-full flex items-center justify-center text-white text-sm ${bg}`}>
      {label}
    </div>
  );
}

type Props = {
  m: Message;
  onApprove?: (approvalId: string) => void;
  onDeny?: (approvalId: string) => void;
};

export default function MessageBubble({ m, onApprove, onDeny }: Props) {
  const isUser = m.role === "user";
  const tsDate = typeof m.ts === "number" ? new Date(m.ts) : new Date(m.ts as any);

  return (
    <div className={clsx("flex w-full gap-3 items-end", isUser ? "justify-end" : "justify-start")}>
      {!isUser && <Avatar role={m.role} />}
      <div
        className={clsx(
          "max-w-[90%] sm:max-w-[75%] rounded-2xl px-4 py-3 shadow-sm leading-6",
          isUser
            ? "bg-indigo-600 text-white"
            : "bg-zinc-100/90 dark:bg-zinc-800/90"
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:m-0 prose-ul:my-2 prose-li:my-0 prose-strong:font-semibold">
          {isUser ? (
            <div className="whitespace-pre-wrap">{m.content}</div>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
          )}
        </div>

        {!isUser && (
          <>
            <TraceChips trace={m.trace || []} />
            <ToolCalls calls={m.tool_calls || []} />

            {m.pending_approval && (
              <div className="mt-3 rounded-lg border border-amber-300/60 bg-amber-50 dark:bg-amber-900/30 dark:border-amber-900/40 p-3 text-xs">
                <div className="font-medium mb-1">Approval required</div>
                <div className="opacity-80 mb-2">{m.pending_approval.reason}</div>
                <pre className="text-[11px] overflow-x-auto">
                  {JSON.stringify(m.pending_approval.args, null, 2)}
                </pre>
                <div className="mt-1 text-[10px] opacity-70">
                  Approval ID: <span className="font-mono">{m.pending_approval.approval_id}</span>
                </div>
                <div className="mt-2 flex gap-2">
                  <button
                    className="px-2 py-1 rounded bg-emerald-600 text-white text-xs"
                    onClick={() => onApprove?.(m.pending_approval!.approval_id)}
                  >
                    Approve
                  </button>
                  <button
                    className="px-2 py-1 rounded bg-rose-600 text-white text-xs"
                    onClick={() => onDeny?.(m.pending_approval!.approval_id)}
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        <div className={clsx("mt-1 text-[10px]", isUser ? "text-white/70" : "text-zinc-500")}>
          {format(tsDate, "p")}
        </div>
      </div>
      {isUser && <Avatar role={m.role} />}
    </div>
  );
}
