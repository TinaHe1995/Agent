import type { ChatMessage, EngineInfo, GateType, PathChoice, Stage, TechChoice } from "../types";
import { ChatPanel } from "./ChatPanel";
import { GateBar } from "./GateBar";

interface LeftSidebarProps {
  engineInfo: EngineInfo;
  stage: Stage;
  projectCompleted: boolean;
  pathEndedBuy: boolean;
  messages: ChatMessage[];
  isAgentTyping: boolean;
  quickReplies: string[];
  onSend: (text: string) => void;
  chatDisabled: boolean;
  pendingGate: GateType;
  pathChoice: PathChoice;
  discoveryReady: boolean;
  requirementsComplete: boolean;
  selectedTechId: TechChoice;
  selectedStyleId: "A" | "B" | null;
  buildDone: boolean;
  acceptanceChecks: [boolean, boolean, boolean];
  stagingReady: boolean;
  goLiveChecks: [boolean, boolean, boolean];
  onConfirmPathSelfBuild: () => void;
  onConfirmPathBuy: () => void;
  onConfirmRequirements: () => void;
  onConfirmStyle: () => void;
  onRequestChanges: () => void;
  onCompleteAcceptance: () => void;
  onConfirmGoLive: () => void;
  onPauseProject: () => void;
  onReset: () => void;
}

export function LeftSidebar({
  engineInfo,
  stage,
  projectCompleted,
  pathEndedBuy,
  messages,
  isAgentTyping,
  quickReplies,
  onSend,
  chatDisabled,
  pendingGate,
  pathChoice,
  discoveryReady,
  requirementsComplete,
  selectedTechId,
  selectedStyleId,
  buildDone,
  acceptanceChecks,
  stagingReady,
  goLiveChecks,
  onConfirmPathSelfBuild,
  onConfirmPathBuy,
  onConfirmRequirements,
  onConfirmStyle,
  onRequestChanges,
  onCompleteAcceptance,
  onConfirmGoLive,
  onPauseProject,
  onReset,
}: LeftSidebarProps) {
  const engineBadge = (() => {
    if (engineInfo.mode === "mock") {
      return { label: "模拟引擎", className: "bg-slate-100 text-slate-600" };
    }
    switch (engineInfo.status) {
      case "ready":
        return { label: "OpenHands 已连接", className: "bg-emerald-100 text-emerald-800" };
      case "checking":
        return { label: "检测引擎…", className: "bg-amber-100 text-amber-800" };
      case "degraded":
        return { label: "引擎未就绪", className: "bg-amber-100 text-amber-800" };
      case "offline":
        return { label: "引擎离线", className: "bg-rose-100 text-rose-800" };
      default:
        return { label: "模拟引擎", className: "bg-slate-100 text-slate-600" };
    }
  })();

  return (
    <aside className="flex h-full max-h-[42vh] min-h-0 w-full flex-col border-b border-slate-200 bg-white lg:max-h-none lg:w-[340px] lg:shrink-0 lg:border-b-0 lg:border-r xl:w-[380px]">
      <div className="border-b border-slate-100 px-4 py-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="text-[11px] font-medium uppercase tracking-wide text-indigo-600">
              Agent 工坊 · MVP
            </div>
            <h1 className="truncate text-base font-semibold text-slate-900">与 Agent 协作</h1>
            <p className="text-xs text-slate-500">项目：内部请假登记工具</p>
            <span
              className={`mt-1.5 inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${engineBadge.className}`}
              title={engineInfo.detail}
            >
              {engineBadge.label}
            </span>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="shrink-0 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            重新开始
          </button>
        </div>
      </div>

      <div className="min-h-0 flex-1 px-3 py-3">
        <ChatPanel
          messages={messages}
          isAgentTyping={isAgentTyping}
          quickReplies={quickReplies}
          onSend={onSend}
          disabled={chatDisabled}
          embedded
        />
      </div>

      <div className="border-t border-slate-100 p-3">
        <GateBar
          stage={stage}
          pendingGate={pendingGate}
          pathChoice={pathChoice}
          discoveryReady={discoveryReady}
          pathEndedBuy={pathEndedBuy}
          requirementsComplete={requirementsComplete}
          selectedTechId={selectedTechId}
          selectedStyleId={selectedStyleId}
          buildDone={buildDone}
          acceptanceChecks={acceptanceChecks}
          stagingReady={stagingReady}
          goLiveChecks={goLiveChecks}
          projectCompleted={projectCompleted}
          onConfirmPathSelfBuild={onConfirmPathSelfBuild}
          onConfirmPathBuy={onConfirmPathBuy}
          onConfirmRequirements={onConfirmRequirements}
          onConfirmStyle={onConfirmStyle}
          onRequestChanges={onRequestChanges}
          onCompleteAcceptance={onCompleteAcceptance}
          onConfirmGoLive={onConfirmGoLive}
          onPauseProject={onPauseProject}
          compact
        />
      </div>
    </aside>
  );
}
