import { CanvasPanel } from "./components/CanvasPanel";
import { ChatPanel, getQuickReplies } from "./components/ChatPanel";
import { GateBar } from "./components/GateBar";
import { StageProgress } from "./components/StageProgress";
import { useAppFlow } from "./useAppFlow";

export default function App() {
  const {
    state,
    currentQuestion,
    sendUserMessage,
    confirmRequirements,
    selectStyle,
    confirmStyle,
    completeProject,
    resetDemo,
    dispatch,
  } = useAppFlow();

  const quickReplies = getQuickReplies(
    state.stage,
    state.requirementsComplete,
    currentQuestion,
  );

  return (
    <div className="flex h-full min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white/90 px-4 py-4 backdrop-blur sm:px-6">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-xs font-medium uppercase tracking-wide text-indigo-600">
              Agent 工坊 · MVP 体验版
            </div>
            <h1 className="text-xl font-semibold text-slate-900">左侧聊天，右侧看成果</h1>
            <p className="text-sm text-slate-500">项目：内部请假登记工具（可交互原型，无需后端）</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <StageProgress
              currentStage={state.stage}
              projectCompleted={state.projectCompleted}
            />
            <button
              type="button"
              onClick={() => void resetDemo()}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              重新开始
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-7xl flex-1 min-h-0 flex-col gap-4 p-4 sm:p-6">
        <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[minmax(320px,2fr)_minmax(380px,3fr)]">
          <ChatPanel
            messages={state.messages}
            isAgentTyping={state.isAgentTyping}
            quickReplies={quickReplies}
            onSend={(text) => void sendUserMessage(text)}
            disabled={state.isAgentTyping || state.projectCompleted}
          />

          <div className="flex min-h-0 flex-col gap-4 overflow-hidden">
            <div className="min-h-0 flex-1 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm">
              <CanvasPanel
                state={state}
                onSelectStyle={selectStyle}
                onToggleAcceptance={(index) =>
                  dispatch({ type: "TOGGLE_ACCEPTANCE", index })
                }
              />
            </div>
          </div>
        </div>

        <GateBar
          stage={state.stage}
          pendingGate={state.pendingGate}
          requirementsComplete={state.requirementsComplete}
          selectedStyleId={state.selectedStyleId}
          buildDone={state.buildDone}
          acceptanceChecks={state.acceptanceChecks}
          projectCompleted={state.projectCompleted}
          onConfirmRequirements={() => void confirmRequirements()}
          onConfirmStyle={() => void confirmStyle()}
          onRequestChanges={() => void sendUserMessage("手机端打不开，请继续修改")}
          onCompleteProject={() => void completeProject()}
        />
      </main>
    </div>
  );
}
