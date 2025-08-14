import { useState } from "react";

type Props = {
  disabled?: boolean;
  onSend: (text: string, extras?: { customerId?: number; from?: string; to?: string; currency?: string }) => void;
};

export default function ChatInput({ disabled, onSend }: Props) {
  const [text, setText] = useState("");
  const [customerId, setCustomerId] = useState<number | "">("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [currency, setCurrency] = useState("USD");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text, {
      customerId: typeof customerId === "number" ? customerId : undefined,
      from: from || undefined,
      to: to || undefined,
      currency: currency || undefined,
    });
    setText("");
  }

  const inputCls = "rounded-xl border border-zinc-200 dark:border-zinc-700 px-3 py-2 bg-white/90 dark:bg-zinc-900/70 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:focus:ring-indigo-700";

  return (
    <form onSubmit={submit} className="flex flex-col gap-2">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <input type="number" placeholder="customerId" value={customerId}
          onChange={(e) => setCustomerId(e.target.value ? Number(e.target.value) : "")}
          className={inputCls}
        />
        <input type="text" placeholder="from (YYYY-MM-DD or ISO)" value={from}
          onChange={(e) => setFrom(e.target.value)} className={inputCls}
        />
        <input type="text" placeholder="to (YYYY-MM-DD or ISO)" value={to}
          onChange={(e) => setTo(e.target.value)} className={inputCls}
        />
        <input type="text" placeholder="currency (USD)" value={currency}
          onChange={(e) => setCurrency(e.target.value)} className={inputCls}
        />
      </div>

      <div className="flex gap-2">
        <input
          autoFocus
          disabled={disabled}
          placeholder="Type a message… e.g., “Show spend for customer 1 last month in USD.”"
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="flex-1 rounded-2xl border border-zinc-200 dark:border-zinc-700 px-4 py-3 bg-white/95 dark:bg-zinc-900/70 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:focus:ring-indigo-700"
        />
        <button
          disabled={disabled || !text.trim()}
          className="rounded-2xl px-5 py-3 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white disabled:opacity-50 shadow"
          type="submit"
        >
          Send
        </button>
      </div>
    </form>
  );
}
