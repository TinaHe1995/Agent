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
  stage: 0,
  messages: [],
  discoveryBrief: "",
  discoveryReady: false,
  pathChoice: null,
  pathEndedBuy: false,
  requirements: initialRequirements,
  requirementsComplete: false,
  requirementsConfirmed: false,
  questionIndex: 0,
  selectedTechId: null,
  selectedStyleId: null,
  styleVersion: 1,
  styleConfirmed: false,
  buildProgress: 0,
  buildDone: false,
  acceptanceChecks: [false, false, false],
  acceptanceCompleted: false,
  stagingProgress: 0,
  stagingReady: false,
  goLiveChecks: [false, false, false],
  projectCompleted: false,
  pendingGate: null,
  conversationId: null,
  sdkConfirmationPending: false,
  workspacePreviewUrl: null,
  workspacePreviewPath: null,
  stagingUrl: null,
  liveUrl: null,
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
    case "UPDATE_DISCOVERY":
      return { ...state, discoveryBrief: action.brief };
    case "SET_DISCOVERY_READY":
      return { ...state, discoveryReady: true, pendingGate: "path" };
    case "SELECT_PATH":
      return { ...state, pathChoice: action.choice };
    case "CONFIRM_PATH_SELF_BUILD":
      return {
        ...state,
        pathChoice: "self_build",
        stage: 1,
        pendingGate: null,
        questionIndex: 0,
        requirements: initialRequirements,
        requirementsComplete: false,
        requirementsConfirmed: false,
      };
    case "CONFIRM_PATH_BUY":
      return {
        ...state,
        pathEndedBuy: true,
        projectCompleted: true,
        pendingGate: null,
      };
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
        selectedTechId: null,
      };
    case "SELECT_TECH":
      return { ...state, selectedTechId: action.techId };
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
        workspacePreviewUrl: null,
        workspacePreviewPath: null,
      };
    case "COMPLETE_ACCEPTANCE":
      return {
        ...state,
        acceptanceCompleted: true,
        stage: 4,
        pendingGate: null,
        stagingProgress: 0,
        stagingReady: false,
        goLiveChecks: [false, false, false],
      };
    case "SET_STAGING_PROGRESS":
      return { ...state, stagingProgress: action.value };
    case "SET_STAGING_READY":
      return {
        ...state,
        stagingReady: true,
        stagingProgress: 100,
        pendingGate: "go_live",
      };
    case "TOGGLE_GO_LIVE_CHECK":
      return {
        ...state,
        goLiveChecks: state.goLiveChecks.map((checked, index) =>
          index === action.index ? !checked : checked,
        ) as AppState["goLiveChecks"],
      };
    case "COMPLETE_GO_LIVE":
      return {
        ...state,
        projectCompleted: true,
        pendingGate: null,
      };
    case "SET_PENDING_GATE":
      return { ...state, pendingGate: action.gate };
    case "SET_CONVERSATION_ID":
      return { ...state, conversationId: action.id };
    case "SET_SDK_CONFIRMATION_PENDING":
      return {
        ...state,
        sdkConfirmationPending: action.value,
      };
    case "SET_WORKSPACE_PREVIEW":
      return {
        ...state,
        workspacePreviewUrl: action.url,
        workspacePreviewPath: action.path ?? null,
      };
    case "SET_STAGING_URL":
      return { ...state, stagingUrl: action.url };
    case "SET_LIVE_URL":
      return { ...state, liveUrl: action.url };
    case "RESET_DEMO":
      return { ...initialState };
    default:
      return state;
  }
}
