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

      <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden p-3 sm:p-4 lg:p-5">
        <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <CanvasPanel
            state={state}
            onSelectStyle={selectStyle}
            onToggleAcceptance={(index) =>
              dispatch({ type: "TOGGLE_ACCEPTANCE", index })
            }
          />
        </div>
      </main>
    </div>
  );
}
