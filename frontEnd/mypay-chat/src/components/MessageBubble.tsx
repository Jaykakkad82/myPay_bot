import type { ReactNode, HTMLAttributes } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { format as formatTime, parseISO, isValid } from "date-fns";
import { clsx } from "clsx";
import type { Message } from "../hooks/useChat";
import TraceChips from "./TraceChips";
import ToolCalls from "./ToolCalls";

/** ---------- Avatar ---------- */
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

/** ---------- Helpers for table cell formatting (frontend-only heuristics) ---------- */
const numberFmt = new Intl.NumberFormat(undefined, { maximumFractionDigits: 6 });

function extractText(children: ReactNode): string {
  if (typeof children === "string" || typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(extractText).join("");
  if (children && typeof children === "object" && "props" in (children as any)) {
    return extractText((children as any).props?.children);
  }
  return "";
}

function isNumericLike(v: string): boolean {
  const s = v.trim();
  return /^-?\d{1,3}(,\d{3})*(\.\d+)?$/.test(s) || /^-?\d+(\.\d+)?$/.test(s);
}

function maybeFormatNumber(v: string): string {
  const clean = v.replace(/,/g, "");
  const n = Number(clean);
  if (!Number.isFinite(n)) return v;
  return numberFmt.format(n);
}

function isIsoDateString(v: string): boolean {
  const s = v.trim();
  if (!/^\d{4}-\d{2}-\d{2}T?\d{0,2}:?\d{0,2}:?\d{0,2}/.test(s)) return false;
  const d = parseISO(s);
  return isValid(d);
}

function formatIsoDate(v: string): string {
  try {
    const d = parseISO(v);
    return isValid(d) ? formatTime(d, "PP p") : v;
  } catch {
    return v;
  }
}

function statusBadge(text: string) {
  const t = text.toUpperCase();
  if (t === "COMPLETED")
    return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200">{text}</span>;
  if (t === "PENDING")
    return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">{text}</span>;
  if (t === "FAILED")
    return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200">{text}</span>;
  return null;
}

/** Render a <td> with number/date/status awareness */
function TdRenderer(
  props: HTMLAttributes<HTMLTableCellElement> & { children?: ReactNode }
) {
  const raw = extractText(props.children);
  const badge = statusBadge(raw);
  const isNum = isNumericLike(raw);
  const isDate = isIsoDateString(raw);

  const display = badge
    ? badge
    : isDate
    ? formatIsoDate(raw)
    : isNum
    ? maybeFormatNumber(raw)
    : raw;

  return (
    <td
      {...props}
      className={clsx(
        "align-middle",
        isNum ? "text-right tabular-nums" : "text-left",
        "max-w-[18rem] truncate",
        props.className
      )}
      title={typeof display === "string" ? display : raw}
    >
      {typeof display === "string" ? <span>{display}</span> : display}
    </td>
  );
}

/** Render a <th> with sticky background (styles in CSS) */
function ThRenderer(props: HTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      {...props}
      className={clsx("text-left font-semibold align-middle", props.className)}
    />
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
          "max-w-[90%] sm:max-w-[72%] rounded-2xl px-4 py-3 shadow-sm",
          isUser ? "bg-indigo-600 text-white" : "bg-zinc-100/90 dark:bg-zinc-800/90"
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:m-0 prose-ul:my-2 prose-li:my-0 prose-strong:font-semibold">
          {isUser ? (
            <div className="whitespace-pre-wrap">{m.content}</div>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: (p) => <table {...p} />,
                thead: (p) => <thead {...p} />,
                tbody: (p) => <tbody {...p} />,
                tr: (p) => <tr {...p} />,
                th: ThRenderer,
                td: TdRenderer,
              }}
            >
              {m.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Assistant-only: trace, tool calls, approvals */}
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
          {formatTime(tsDate, "p")}
        </div>
      </div>
      {isUser && <Avatar role={m.role} />}
    </div>
  );
}
