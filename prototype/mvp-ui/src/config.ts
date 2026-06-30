/**
 * Runtime config from Vite env.
 *
 * VITE_USE_MOCK=true  → full mock flow (default, no backend)
 * VITE_USE_MOCK=false → stage 3+ uses openhands-agent-server when reachable
 */

function parseBool(value: string | undefined, defaultValue: boolean): boolean {
  if (value === undefined || value === "") return defaultValue;
  return value === "1" || value.toLowerCase() === "true";
}

/** Default true so GitHub Pages works without a backend. */
export const USE_MOCK = parseBool(import.meta.env.VITE_USE_MOCK, true);

/** Agent Server origin. In dev, vite proxy can use relative `/api`. */
export const AGENT_SERVER_URL = (
  import.meta.env.VITE_AGENT_SERVER_URL ?? ""
).replace(/\/$/, "");

/**
 * Optional session API key (never commit real keys).
 * Sent as `x-session-api-key` and WebSocket `session_api_key`.
 */
export const AGENT_SESSION_API_KEY =
  import.meta.env.VITE_AGENT_SESSION_API_KEY ?? "";

/** Workspace directory on the server host for build conversations. */
export const AGENT_WORKSPACE_DIR =
  import.meta.env.VITE_AGENT_WORKSPACE_DIR ?? "";

export type EngineMode = "mock" | "live";

export function getEngineMode(): EngineMode {
  return USE_MOCK ? "mock" : "live";
}

export function resolveApiBase(): string {
  if (AGENT_SERVER_URL) return AGENT_SERVER_URL;
  // Vite dev proxy: requests go to same origin /api → localhost:8000
  return "";
}
