/**
 * OpenHands Agent Server HTTP + WebSocket client (skeleton).
 *
 * Used when VITE_USE_MOCK=false. Stages 0–2 stay on mockAgent; stage 3+ can
 * delegate build / chat to a running `uv run agent-server`.
 */

import {
  AGENT_SESSION_API_KEY,
  AGENT_WORKSPACE_DIR,
  resolveApiBase,
} from "../config";
import type { RequirementsData } from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AgentServerHealth = "alive" | "ready" | "unreachable";

export interface ConversationInfo {
  id: string;
  execution_status?: string;
}

export interface SendMessagePayload {
  role: "user" | "assistant" | "system";
  content: string;
  run?: boolean;
}

export type AgentEventHandler = (event: unknown) => void;

export class AgentServerError extends Error {
  status?: number;
  body?: string;

  constructor(message: string, status?: number, body?: string) {
    super(message);
    this.name = "AgentServerError";
    this.status = status;
    this.body = body;
  }
}

// ---------------------------------------------------------------------------
// URL helpers
// ---------------------------------------------------------------------------

function apiUrl(path: string): string {
  const base = resolveApiBase();
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalized}`;
}

function wsUrl(path: string): string {
  const base = resolveApiBase();
  if (base) {
    const url = new URL(base);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    return `${url.origin}${path}`;
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}${path}`;
}

function authHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (AGENT_SESSION_API_KEY) {
    headers["x-session-api-key"] = AGENT_SESSION_API_KEY;
  }
  return headers;
}

async function parseError(res: Response): Promise<AgentServerError> {
  const body = await res.text().catch(() => "");
  return new AgentServerError(
    `Agent Server ${res.status}: ${body || res.statusText}`,
    res.status,
    body,
  );
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export async function checkAgentServerHealth(): Promise<{
  health: AgentServerHealth;
  detail?: string;
}> {
  try {
    const aliveRes = await fetch(apiUrl("/alive"), {
      headers: authHeaders(),
    });
    if (!aliveRes.ok) {
      return { health: "unreachable", detail: await aliveRes.text() };
    }

    const readyRes = await fetch(apiUrl("/ready"), {
      headers: authHeaders(),
    });
    if (readyRes.ok) {
      return { health: "ready" };
    }
    return { health: "alive", detail: "Server up but not ready (503)" };
  } catch (err) {
    return {
      health: "unreachable",
      detail: err instanceof Error ? err.message : String(err),
    };
  }
}

// ---------------------------------------------------------------------------
// Conversations
// ---------------------------------------------------------------------------

function toMessageContent(text: string) {
  return [{ type: "text", text }];
}

export function buildGoalFromRequirements(
  requirements: RequirementsData,
  styleHint?: string,
): string {
  const lines = [
    "你是 Agent 工坊的执行 Agent。请根据以下已确认需求，在当前 workspace 里实现一个可运行的 Web 小应用原型。",
    "",
    `目标：${requirements.goal || "（未填写）"}`,
    `用户：${requirements.users || "（未填写）"}`,
    `P0 功能：${requirements.p0Features.join("、") || "（未填写）"}`,
    `验收标准：${requirements.acceptance.join("；") || "（未填写）"}`,
    `不做：${requirements.outOfScope.join("、") || "无"}`,
    `时间期望：${requirements.timeline || "尽快"}`,
  ];
  if (styleHint) {
    lines.push("", `界面风格：${styleHint}`);
  }
  lines.push(
    "",
    "要求：优先做出可本地打开的单页或静态站点；完成后用简短中文说明如何试用。",
  );
  return lines.join("\n");
}

export interface StartBuildConversationOptions {
  requirements: RequirementsData;
  styleLabel?: string;
  workingDir?: string;
}

export async function startBuildConversation(
  options: StartBuildConversationOptions,
): Promise<ConversationInfo> {
  const goal = buildGoalFromRequirements(
    options.requirements,
    options.styleLabel,
  );
  const workingDir =
    options.workingDir ||
    AGENT_WORKSPACE_DIR ||
    `mvp-ui-build-${Date.now()}`;

  const body = {
    agent: {
      kind: "Agent",
      llm: {
        usage_id: "mvp-ui-build",
        model: import.meta.env.VITE_LLM_MODEL ?? "gpt-4o",
      },
      tools: [
        { name: "terminal" },
        { name: "file_editor" },
        { name: "task_tracker" },
      ],
    },
    workspace: {
      working_dir: workingDir,
    },
    confirmation_policy: {
      kind: "ConfirmRisky",
      threshold: "high",
      confirm_unknown: true,
    },
    initial_message: {
      role: "user",
      content: toMessageContent(goal),
      run: true,
    },
  };

  const res = await fetch(apiUrl("/api/conversations"), {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });

  if (!res.ok) throw await parseError(res);
  return (await res.json()) as ConversationInfo;
}

export async function sendConversationMessage(
  conversationId: string,
  payload: SendMessagePayload,
): Promise<void> {
  const res = await fetch(
    apiUrl(`/api/conversations/${conversationId}/events`),
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        role: payload.role,
        content: toMessageContent(payload.content),
        run: payload.run ?? true,
      }),
    },
  );
  if (!res.ok) throw await parseError(res);
}

export async function runConversation(conversationId: string): Promise<void> {
  const res = await fetch(
    apiUrl(`/api/conversations/${conversationId}/run`),
    { method: "POST", headers: authHeaders() },
  );
  if (!res.ok) throw await parseError(res);
}

export async function getConversation(
  conversationId: string,
): Promise<ConversationInfo> {
  const res = await fetch(apiUrl(`/api/conversations/${conversationId}`), {
    headers: authHeaders(),
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as ConversationInfo;
}

export async function getAgentFinalResponse(
  conversationId: string,
): Promise<string> {
  const res = await fetch(
    apiUrl(`/api/conversations/${conversationId}/agent_final_response`),
    { headers: authHeaders() },
  );
  if (!res.ok) throw await parseError(res);
  const data = (await res.json()) as { response?: string; text?: string };
  return data.response ?? data.text ?? "";
}

export async function deleteConversation(
  conversationId: string,
): Promise<void> {
  const res = await fetch(apiUrl(`/api/conversations/${conversationId}`), {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok && res.status !== 404) throw await parseError(res);
}

export async function respondToConfirmation(
  conversationId: string,
  accept: boolean,
  reason?: string,
): Promise<void> {
  const res = await fetch(
    apiUrl(`/api/conversations/${conversationId}/events/respond_to_confirmation`),
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ accept, reason }),
    },
  );
  if (!res.ok) throw await parseError(res);
}

// ---------------------------------------------------------------------------
// WebSocket events
// ---------------------------------------------------------------------------

export function subscribeToConversationEvents(
  conversationId: string,
  onEvent: AgentEventHandler,
  onError?: (err: Event) => void,
): () => void {
  const params = new URLSearchParams();
  if (AGENT_SESSION_API_KEY) {
    params.set("session_api_key", AGENT_SESSION_API_KEY);
  }
  const qs = params.toString();
  const path = `/sockets/events/${conversationId}${qs ? `?${qs}` : ""}`;
  const socket = new WebSocket(wsUrl(path));

  socket.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data as string) as unknown;
      onEvent(data);
    } catch {
      onEvent(msg.data);
    }
  };

  socket.onerror = (ev) => onError?.(ev);

  return () => {
    if (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    ) {
      socket.close();
    }
  };
}

// ---------------------------------------------------------------------------
// Event parsing helpers
// ---------------------------------------------------------------------------

export function getEventKind(event: unknown): string {
  if (!event || typeof event !== "object") return "";
  const e = event as Record<string, unknown>;
  return String(e.kind ?? e.type ?? e.event_type ?? "");
}

export function extractAgentMessageText(event: unknown): string | null {
  if (!event || typeof event !== "object") return null;
  const e = event as Record<string, unknown>;
  const kind = getEventKind(event).toLowerCase();

  if (!kind.includes("message")) return null;

  const role = String(e.role ?? "").toLowerCase();
  if (role && role !== "assistant" && role !== "agent") return null;

  if (typeof e.content === "string" && e.content.trim()) return e.content.trim();

  if (Array.isArray(e.content)) {
    const parts = e.content
      .map((block) => {
        if (!block || typeof block !== "object") return "";
        const b = block as Record<string, unknown>;
        if (b.type === "text" && typeof b.text === "string") return b.text;
        return "";
      })
      .filter(Boolean);
    if (parts.length) return parts.join("\n");
  }

  if (typeof e.text === "string" && e.text.trim()) return e.text.trim();
  return null;
}

export function isToolActionEvent(event: unknown): boolean {
  const kind = getEventKind(event).toLowerCase();
  return kind.includes("action") && !kind.includes("observation");
}

export function isAgentFinishedEvent(event: unknown): boolean {
  const kind = getEventKind(event).toLowerCase();
  if (kind.includes("finish")) return true;
  if (!event || typeof event !== "object") return false;
  const e = event as Record<string, unknown>;
  const action = e.action;
  if (action && typeof action === "object") {
    const a = action as Record<string, unknown>;
    return String(a.kind ?? "").toLowerCase().includes("finish");
  }
  return false;
}

export function isConfirmationPendingEvent(event: unknown): boolean {
  if (eventImpliesConfirmationWait(event)) return true;
  const kind = getEventKind(event).toLowerCase();
  return kind.includes("confirmation") || kind.includes("confirm");
}

// ---------------------------------------------------------------------------
// Execution status + workspace preview
// ---------------------------------------------------------------------------

export type WorkspacePreview = {
  url: string;
  path: string;
};

export function parseExecutionStatus(info: ConversationInfo): string | undefined {
  const raw = info.execution_status;
  if (typeof raw === "string") return raw;
  if (raw && typeof raw === "object" && "value" in raw) {
    const v = (raw as { value?: unknown }).value;
    return typeof v === "string" ? v : undefined;
  }
  return undefined;
}

export function isWaitingForConfirmationStatus(status: string | undefined): boolean {
  return status === "waiting_for_confirmation" || status === "WAITING_FOR_CONFIRMATION";
}

export function isWaitingForConfirmation(info: ConversationInfo): boolean {
  return isWaitingForConfirmationStatus(parseExecutionStatus(info));
}

/** Static workspace file URL served by agent server. */
export function getWorkspaceFileUrl(conversationId: string, filePath: string): string {
  const normalized = filePath.replace(/^\/+/, "");
  return apiUrl(`/api/conversations/${conversationId}/workspace/${normalized}`);
}

const PREVIEW_CANDIDATES = [
  "index.html",
  "dist/index.html",
  "build/index.html",
  "public/index.html",
  "preview/index.html",
];

/** Probe common HTML entry points in the agent workspace. */
export async function probeWorkspacePreview(
  conversationId: string,
): Promise<WorkspacePreview | null> {
  for (const path of PREVIEW_CANDIDATES) {
    const url = getWorkspaceFileUrl(conversationId, path);
    try {
      const res = await fetch(url, { method: "HEAD", headers: authHeaders() });
      if (res.ok) return { url, path };
      const getRes = await fetch(url, {
        method: "GET",
        headers: { ...authHeaders(), Range: "bytes=0-0" },
      });
      if (getRes.ok) return { url, path };
    } catch {
      /* try next */
    }
  }
  return null;
}

export function eventImpliesConfirmationWait(event: unknown): boolean {
  if (!event || typeof event !== "object") return false;
  const e = event as Record<string, unknown>;
  const kind = getEventKind(event);

  if (kind === "ConversationStateUpdateEvent") {
    const key = String(e.key ?? "");
    const value = e.value;
    if (key === "execution_status") {
      if (typeof value === "string") {
        return isWaitingForConfirmationStatus(value);
      }
      if (value && typeof value === "object" && "value" in value) {
        const inner = (value as { value?: unknown }).value;
        return typeof inner === "string" && isWaitingForConfirmationStatus(inner);
      }
    }
  }

  if (kind === "PauseEvent" && e.reason === "Confirmation") return true;
  return false;
}

export const STAGING_PREP_MESSAGE =
  "验收已通过。请在 workspace 中执行构建/打包，确保 dist 或 build 目录有可访问的 index.html，用于测试环境部署。";

export const LIVE_PREP_MESSAGE =
  "测试环境已验证。请整理最终交付物，并确认正式环境入口页面可访问。";
