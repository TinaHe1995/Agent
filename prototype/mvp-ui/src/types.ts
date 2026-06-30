export type Stage = 0 | 1 | 2 | 3 | 4;

export type GateType =
  | "path"
  | "requirements"
  | "style"
  | "acceptance"
  | "go_live"
  | "sdk_confirm"
  | null;

export type PathChoice = "self_build" | "saas" | "low_code" | null;

export type TechChoice = "web" | "wechat" | "desktop" | null;

export type EngineMode = "mock" | "live";

export type EngineStatus = "mock" | "checking" | "ready" | "degraded" | "offline";

export interface EngineInfo {
  mode: EngineMode;
  status: EngineStatus;
  detail?: string;
}

export type MessageRole = "agent" | "user";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
}

export interface RequirementsData {
  goal: string;
  users: string;
  p0Features: string[];
  p1Features: string[];
  acceptance: string[];
  outOfScope: string[];
  timeline: string;
}

export interface StyleOption {
  id: "A" | "B";
  name: string;
  description: string;
  colors: string[];
  recommended?: boolean;
}

export interface AppState {
  stage: Stage;
  messages: ChatMessage[];
  discoveryBrief: string;
  discoveryReady: boolean;
  pathChoice: PathChoice;
  pathEndedBuy: boolean;
  requirements: RequirementsData;
  requirementsComplete: boolean;
  requirementsConfirmed: boolean;
  questionIndex: number;
  selectedTechId: TechChoice;
  selectedStyleId: "A" | "B" | null;
  styleVersion: number;
  styleConfirmed: boolean;
  buildProgress: number;
  buildDone: boolean;
  acceptanceChecks: [boolean, boolean, boolean];
  acceptanceCompleted: boolean;
  stagingProgress: number;
  stagingReady: boolean;
  goLiveChecks: [boolean, boolean, boolean];
  projectCompleted: boolean;
  pendingGate: GateType;
  conversationId: string | null;
  sdkConfirmationPending: boolean;
  workspacePreviewUrl: string | null;
  workspacePreviewPath: string | null;
  stagingUrl: string | null;
  liveUrl: string | null;
  isAgentTyping: boolean;
  styleWarmth: number;
  styleButtonSize: number;
}

export type AppAction =
  | { type: "ADD_MESSAGE"; message: ChatMessage }
  | { type: "SET_AGENT_TYPING"; value: boolean }
  | { type: "UPDATE_DISCOVERY"; brief: string }
  | { type: "SET_DISCOVERY_READY" }
  | { type: "SELECT_PATH"; choice: PathChoice }
  | { type: "CONFIRM_PATH_SELF_BUILD" }
  | { type: "CONFIRM_PATH_BUY" }
  | { type: "UPDATE_REQUIREMENTS"; patch: Partial<RequirementsData> }
  | { type: "NEXT_QUESTION" }
  | { type: "SET_REQUIREMENTS_COMPLETE" }
  | { type: "CONFIRM_REQUIREMENTS" }
  | { type: "SELECT_TECH"; techId: TechChoice }
  | { type: "SELECT_STYLE"; styleId: "A" | "B" }
  | { type: "CONFIRM_STYLE" }
  | { type: "ADJUST_STYLE"; warmth?: number; buttonSize?: number }
  | { type: "SET_BUILD_PROGRESS"; value: number }
  | { type: "SET_BUILD_DONE" }
  | { type: "TOGGLE_ACCEPTANCE"; index: number }
  | { type: "REQUEST_CHANGES" }
  | { type: "COMPLETE_ACCEPTANCE" }
  | { type: "SET_STAGING_PROGRESS"; value: number }
  | { type: "SET_STAGING_READY" }
  | { type: "TOGGLE_GO_LIVE_CHECK"; index: number }
  | { type: "COMPLETE_GO_LIVE" }
  | { type: "SET_PENDING_GATE"; gate: GateType }
  | { type: "SET_CONVERSATION_ID"; id: string | null }
  | { type: "SET_SDK_CONFIRMATION_PENDING"; value: boolean }
  | {
      type: "SET_WORKSPACE_PREVIEW";
      url: string | null;
      path?: string | null;
    }
  | { type: "SET_STAGING_URL"; url: string | null }
  | { type: "SET_LIVE_URL"; url: string | null }
  | { type: "RESET_DEMO" };
