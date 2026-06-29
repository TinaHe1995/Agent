export type Stage = 1 | 2 | 3;

export type GateType = "requirements" | "style" | "acceptance" | null;

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
  requirements: RequirementsData;
  requirementsComplete: boolean;
  requirementsConfirmed: boolean;
  questionIndex: number;
  selectedStyleId: "A" | "B" | null;
  styleVersion: number;
  styleConfirmed: boolean;
  buildProgress: number;
  buildDone: boolean;
  acceptanceChecks: [boolean, boolean, boolean];
  projectCompleted: boolean;
  pendingGate: GateType;
  isAgentTyping: boolean;
  styleWarmth: number;
  styleButtonSize: number;
}

export type AppAction =
  | { type: "ADD_MESSAGE"; message: ChatMessage }
  | { type: "SET_AGENT_TYPING"; value: boolean }
  | { type: "UPDATE_REQUIREMENTS"; patch: Partial<RequirementsData> }
  | { type: "NEXT_QUESTION" }
  | { type: "SET_REQUIREMENTS_COMPLETE" }
  | { type: "CONFIRM_REQUIREMENTS" }
  | { type: "SELECT_STYLE"; styleId: "A" | "B" }
  | { type: "CONFIRM_STYLE" }
  | { type: "ADJUST_STYLE"; warmth?: number; buttonSize?: number }
  | { type: "SET_BUILD_PROGRESS"; value: number }
  | { type: "SET_BUILD_DONE" }
  | { type: "TOGGLE_ACCEPTANCE"; index: number }
  | { type: "REQUEST_CHANGES" }
  | { type: "COMPLETE_PROJECT" }
  | { type: "SET_PENDING_GATE"; gate: GateType }
  | { type: "RESET_DEMO" };
