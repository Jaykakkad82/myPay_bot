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
  notifications?: any[];
};

export type ChatRequest = {
  // sessionId no longer required (header is preferred), but kept for compatibility
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

// Session endpoints
export type SessionStartResponse = {
  sessionId: string;
  tier: "anonymous" | "elevated" | "admin" | string;
  limits?: SessionLimitsResponse["limits"]
};

export type SessionLimitsResponse = {
  sessionId: string;
  tier: string;
  limits: {
    requests?: { used: number; max: number };
    tools?: { used: number; max: number };
    tokens?: { used: number; max: number };
  };
};

// ---------- Base URL handling ----------
const RAW_BASE: string =
  (import.meta as any)?.env?.VITE_AGENT_API_URL ?? "";

const joinURL = (base: string, path: string) =>
  `${base.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;

const BASE = RAW_BASE || "http://localhost:8010";

// ---------- Session header helpers ----------
const SESSION_KEY = "mp_server_session_id";

export function getSessionId(): string | null {
  return localStorage.getItem(SESSION_KEY);
}
export function setSessionId(id: string) {
  localStorage.setItem(SESSION_KEY, id);
}
export function clearSessionId() {
  localStorage.removeItem(SESSION_KEY);
}


// ---------- Common fetch wrapper ----------
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = BASE ? joinURL(BASE, path) : path;
  const sessionId = getSessionId();
  const res = await fetch(url, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(sessionId ? { "X-Session-Id": sessionId } : {}),
      ...(init?.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, `${res.status} ${res.statusText}`, text);
  }
  return res.json() as Promise<T>;
}

// ---------- API calls ----------
export async function health(): Promise<{ ok: boolean }> {
  try {
    return await apiFetch<{ ok: boolean }>("/health");
  } catch {
    return { ok: false };
  }
}

// Server-issued session
export async function startSession(): Promise<SessionStartResponse> {
  const r = await apiFetch<SessionStartResponse>("/session/start", {
    method: "POST",
    body: JSON.stringify({}),
  });
  if (r?.sessionId) setSessionId(r.sessionId);
  return r;
}

export async function getLimits(): Promise<SessionLimitsResponse> {
  return apiFetch<SessionLimitsResponse>("/session/limits");
}

export async function upgradeSession(accessKey: string): Promise<SessionStartResponse> {
  const r = await apiFetch<SessionStartResponse>("/session/upgrade", {
    method: "POST",
    body: JSON.stringify({ accessKey }),
  });
  if (r?.sessionId) setSessionId(r.sessionId);
  return r;
}

// Chat + approvals (header carries session)
export async function sendChat(
  text: string,
  extras?: { customerId?: number; from?: string; to?: string; currency?: string },
  // optional compatibility param—unused if header is present
  sessionId?: string
): Promise<AssistantMessage> {
  const body: ChatRequest = { sessionId, message: text, extras };
  return apiFetch<AssistantMessage>("/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function approve(approvalId: string, lastState: any): Promise<AssistantMessage> {
  return apiFetch<AssistantMessage>("/workflow/approval", {
    method: "POST",
    body: JSON.stringify({ approvalId, decision: "APPROVE", lastState }),
  });
}

export async function deny(approvalId: string, lastState: any): Promise<AssistantMessage> {
  return apiFetch<AssistantMessage>("/workflow/approval", {
    method: "POST",
    body: JSON.stringify({ approvalId, decision: "DENY", lastState }),
  });
}



// ---------- Error type with status ----------
export class ApiError extends Error {
  status: number;
  bodyText?: string;
  constructor(status: number, message: string, bodyText?: string) {
    super(message);
    this.status = status;
    this.bodyText = bodyText;
  }
}
