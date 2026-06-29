export type Stage = 0 | 1 | 2 | 3 | 4;

export type GateType =
  | "path"
  | "requirements"
  | "style"
  | "acceptance"
  | "go_live"
  | null;

export type PathChoice = "self_build" | "saas" | "low_code" | null;

export type TechChoice = "web" | "wechat" | "desktop" | null;

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
  | { type: "RESET_DEMO" };
