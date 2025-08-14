import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { format } from "date-fns";
import { clsx } from "clsx";
import type { Message } from "../hooks/useChat";

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

export default function MessageBubble({ m }: { m: Message }) {
  const isUser = m.role === "user";

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
        <div className={clsx("mt-1 text-[10px]", isUser ? "text-white/70" : "text-zinc-500")}>
          {format(new Date(m.ts), "p")}
        </div>
      </div>
      {isUser && <Avatar role={m.role} />}
    </div>
  );
}
