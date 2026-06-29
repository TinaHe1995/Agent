import type { ChatMessage, GateType, Stage } from "../types";
import { ChatPanel } from "./ChatPanel";
import { GateBar } from "./GateBar";

interface LeftSidebarProps {
  stage: Stage;
  projectCompleted: boolean;
  messages: ChatMessage[];
  isAgentTyping: boolean;
  quickReplies: string[];
  onSend: (text: string) => void;
  chatDisabled: boolean;
  pendingGate: GateType;
  requirementsComplete: boolean;
  selectedStyleId: "A" | "B" | null;
  buildDone: boolean;
  acceptanceChecks: [boolean, boolean, boolean];
  onConfirmRequirements: () => void;
  onConfirmStyle: () => void;
  onRequestChanges: () => void;
  onCompleteProject: () => void;
  onReset: () => void;
}

export function LeftSidebar({
  stage,
  projectCompleted,
  messages,
  isAgentTyping,
  quickReplies,
  onSend,
  chatDisabled,
  pendingGate,
  requirementsComplete,
  selectedStyleId,
  buildDone,
  acceptanceChecks,
  onConfirmRequirements,
  onConfirmStyle,
  onRequestChanges,
  onCompleteProject,
  onReset,
}: LeftSidebarProps) {
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
          requirementsComplete={requirementsComplete}
          selectedStyleId={selectedStyleId}
          buildDone={buildDone}
          acceptanceChecks={acceptanceChecks}
          projectCompleted={projectCompleted}
          onConfirmRequirements={onConfirmRequirements}
          onConfirmStyle={onConfirmStyle}
          onRequestChanges={onRequestChanges}
          onCompleteProject={onCompleteProject}
          compact
        />
      </div>
    </aside>
  );
}
