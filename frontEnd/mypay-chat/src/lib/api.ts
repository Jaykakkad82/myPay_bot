export type ChatRequest = {
  sessionId: string;
  message: string;
  customerId?: number;
  from?: string;
  to?: string;
  currency?: string;
};

export type ChatResponse = {
  answer: string;
};

const BASE = import.meta.env.VITE_AGENT_API_URL || "http://localhost:8000";

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Chat API ${res.status}: ${text}`);
  }
  return res.json();
}

export async function health(): Promise<{ ok: boolean }> {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}
