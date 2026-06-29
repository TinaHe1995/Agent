import type { AppAction, AppState, RequirementsData } from "./types";

export const initialRequirements: RequirementsData = {
  goal: "",
  users: "",
  p0Features: [],
  p1Features: [],
  acceptance: [],
  outOfScope: [],
  timeline: "",
};

export const initialState: AppState = {
  stage: 1,
  messages: [],
  requirements: initialRequirements,
  requirementsComplete: false,
  requirementsConfirmed: false,
  questionIndex: 0,
  selectedStyleId: null,
  styleVersion: 1,
  styleConfirmed: false,
  buildProgress: 0,
  buildDone: false,
  acceptanceChecks: [false, false, false],
  projectCompleted: false,
  pendingGate: null,
  isAgentTyping: false,
  styleWarmth: 50,
  styleButtonSize: 50,
};

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "ADD_MESSAGE":
      return { ...state, messages: [...state.messages, action.message] };
    case "SET_AGENT_TYPING":
      return { ...state, isAgentTyping: action.value };
    case "UPDATE_REQUIREMENTS":
      return {
        ...state,
        requirements: { ...state.requirements, ...action.patch },
      };
    case "NEXT_QUESTION":
      return { ...state, questionIndex: state.questionIndex + 1 };
    case "SET_REQUIREMENTS_COMPLETE":
      return {
        ...state,
        requirementsComplete: true,
        pendingGate: "requirements",
      };
    case "CONFIRM_REQUIREMENTS":
      return {
        ...state,
        requirementsConfirmed: true,
        stage: 2,
        pendingGate: null,
        selectedStyleId: null,
      };
    case "SELECT_STYLE":
      return { ...state, selectedStyleId: action.styleId };
    case "CONFIRM_STYLE":
      return {
        ...state,
        styleConfirmed: true,
        stage: 3,
        pendingGate: null,
        buildProgress: 0,
        buildDone: false,
      };
    case "ADJUST_STYLE":
      return {
        ...state,
        styleVersion: state.styleVersion + 1,
        styleWarmth: action.warmth ?? state.styleWarmth,
        styleButtonSize: action.buttonSize ?? state.styleButtonSize,
        pendingGate: "style",
      };
    case "SET_BUILD_PROGRESS":
      return { ...state, buildProgress: action.value };
    case "SET_BUILD_DONE":
      return {
        ...state,
        buildDone: true,
        buildProgress: 100,
        pendingGate: "acceptance",
      };
    case "TOGGLE_ACCEPTANCE":
      return {
        ...state,
        acceptanceChecks: state.acceptanceChecks.map((checked, index) =>
          index === action.index ? !checked : checked,
        ) as AppState["acceptanceChecks"],
      };
    case "REQUEST_CHANGES":
      return {
        ...state,
        buildDone: false,
        buildProgress: 0,
        acceptanceChecks: [false, false, false],
        pendingGate: null,
      };
    case "COMPLETE_PROJECT":
      return {
        ...state,
        projectCompleted: true,
        pendingGate: null,
      };
    case "SET_PENDING_GATE":
      return { ...state, pendingGate: action.gate };
    case "RESET_DEMO":
      return { ...initialState };
    default:
      return state;
  }
}
