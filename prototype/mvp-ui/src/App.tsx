import { CanvasPanel } from "./components/CanvasPanel";
import { LeftSidebar } from "./components/LeftSidebar";
import { getQuickReplies } from "./components/ChatPanel";
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
    <div className="flex h-screen min-h-0 flex-col overflow-hidden bg-slate-100 lg:flex-row">
      <LeftSidebar
        stage={state.stage}
        projectCompleted={state.projectCompleted}
        messages={state.messages}
        isAgentTyping={state.isAgentTyping}
        quickReplies={quickReplies}
        onSend={(text) => void sendUserMessage(text)}
        chatDisabled={state.isAgentTyping || state.projectCompleted}
        pendingGate={state.pendingGate}
        requirementsComplete={state.requirementsComplete}
        selectedStyleId={state.selectedStyleId}
        buildDone={state.buildDone}
        acceptanceChecks={state.acceptanceChecks}
        onConfirmRequirements={() => void confirmRequirements()}
        onConfirmStyle={() => void confirmStyle()}
        onRequestChanges={() => void sendUserMessage("手机端打不开，请继续修改")}
        onCompleteProject={() => void completeProject()}
        onReset={() => void resetDemo()}
      />

      <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden p-4 sm:p-5 lg:p-6">
        <div className="flex h-full min-h-0 flex-col rounded-2xl border border-slate-200 bg-slate-50 p-4 shadow-sm sm:p-5 lg:p-6">
          <div className="mb-4 shrink-0 border-b border-slate-200 pb-3">
            <div className="text-xs font-medium uppercase tracking-wide text-violet-600">
              成果画布
            </div>
            <h2 className="text-lg font-semibold text-slate-900">通过 Tab 切换查看各部分内容</h2>
          </div>
          <div className="min-h-0 flex-1">
            <CanvasPanel
              state={state}
              onSelectStyle={selectStyle}
              onToggleAcceptance={(index) =>
                dispatch({ type: "TOGGLE_ACCEPTANCE", index })
              }
            />
          </div>
        </div>
      </main>
    </div>
  );
}
