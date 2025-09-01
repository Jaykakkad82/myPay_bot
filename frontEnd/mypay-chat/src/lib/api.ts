
// ---------- Types ----------
export type TraceStep = { node: string; status: string; details?: any };
export type ToolCall = { tool: string; args: any };

export type AssistantMessage = {
  id: string;
  role: "assistant";
  content: string; // markdown
  trace?: TraceStep[];
  tool_calls?: ToolCall[];
  pending_approval?: { reason: string; args: any; approval_id: string } | null;
  ts: string | number; // server may return ISO or epoch; UI handles both
  resume?: any;
};

// Optional legacy types (if any old code still imports them)
export type ChatRequest = {
  sessionId?: string;
  message: string;
  extras?: {
    customerId?: number;
    from?: string;
    to?: string;
    currency?: string;
  };
};
export type ChatResponse = { answer: string }; // legacy only

// ---------- Base URL handling ----------
const RAW_BASE: string =
  (import.meta as any)?.env?.VITE_AGENT_API_URL ??
  ""; // empty string => same-origin

// join helper to avoid // issues
const joinURL = (base: string, path: string) =>
  `${base.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;

// If RAW_BASE is empty, use same-origin relative paths.
// If you prefer explicit localhost fallback, set RAW_BASE || "http://localhost:8000"
const BASE = RAW_BASE || "http://localhost:8010";
// const BASE = "http://localhost:8000";

// Common fetch wrapper
async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = BASE ? joinURL(BASE, path) : path;
  const res = await fetch(url, {
    // include credentials if your backend uses cookies/sessions:
    // credentials: "include",
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} – ${text}`.trim());
  }
  console.log("API Fetch: ", url, init);
  return res.json() as Promise<T>;
}

// ---------- API calls ----------
export async function health(): Promise<{ ok: boolean }> {
  try {
    // Works with either absolute BASE or same-origin
    return await apiFetch<{ ok: boolean }>("/health");
  } catch {
    return { ok: false };
  }
}

export async function sendChat(
  text: string,
  extras?: { customerId?: number; from?: string; to?: string; currency?: string },
  sessionId?: string
): Promise<AssistantMessage> {
  const body: ChatRequest = {
    sessionId,
    message: text,
    extras,
  };
  return apiFetch<AssistantMessage>("/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function approve(
  approvalId: string,
  lastState: any
): Promise<AssistantMessage> {
  return apiFetch<AssistantMessage>("/workflow/approval", {
    method: "POST",
    body: JSON.stringify({
      approvalId,
      decision: "APPROVE",
      lastState,
    }),
  });
}

export async function deny(
  approvalId: string,
  lastState: any
): Promise<AssistantMessage> {
  return apiFetch<AssistantMessage>("/workflow/approval", {
    method: "POST",
    body: JSON.stringify({
      approvalId,
      decision: "DENY",
      lastState,
    }),
  });
}
