/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_USE_MOCK?: string;
  readonly VITE_AGENT_SERVER_URL?: string;
  readonly VITE_AGENT_SESSION_API_KEY?: string;
  readonly VITE_AGENT_WORKSPACE_DIR?: string;
  readonly VITE_LLM_MODEL?: string;
  readonly VITE_BASE_PATH?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
