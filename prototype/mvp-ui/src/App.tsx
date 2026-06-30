import { CanvasPanel } from "./components/CanvasPanel";
import { LeftSidebar } from "./components/LeftSidebar";
import { getQuickReplies } from "./components/ChatPanel";
import { useAppFlow } from "./useAppFlow";

export default function App() {
  const {
    state,
    engineInfo,
    currentQuestion,
    currentDiscoveryStep,
    sendUserMessage,
    selectPath,
    confirmPathSelfBuild,
    confirmPathBuy,
    confirmRequirements,
    selectTech,
    selectStyle,
    confirmStyle,
    completeAcceptance,
    confirmGoLive,
    pauseProject,
    resetDemo,
    dispatch,
  } = useAppFlow();

  const quickReplies = getQuickReplies(
    state.stage,
    state.discoveryReady,
    state.requirementsComplete,
    state.questionIndex,
    currentQuestion,
    currentDiscoveryStep,
  );

  return (
    <div className="flex h-screen min-h-0 flex-col overflow-hidden bg-slate-100 lg:flex-row">
        <LeftSidebar
          engineInfo={engineInfo}
          stage={state.stage}
        projectCompleted={state.projectCompleted}
        pathEndedBuy={state.pathEndedBuy}
        messages={state.messages}
        isAgentTyping={state.isAgentTyping}
        quickReplies={quickReplies}
        onSend={(text) => void sendUserMessage(text)}
        chatDisabled={state.isAgentTyping || state.projectCompleted}
        pendingGate={state.pendingGate}
        pathChoice={state.pathChoice}
        discoveryReady={state.discoveryReady}
        requirementsComplete={state.requirementsComplete}
        selectedTechId={state.selectedTechId}
        selectedStyleId={state.selectedStyleId}
        buildDone={state.buildDone}
        acceptanceChecks={state.acceptanceChecks}
        stagingReady={state.stagingReady}
        goLiveChecks={state.goLiveChecks}
        onConfirmPathSelfBuild={() => void confirmPathSelfBuild()}
        onConfirmPathBuy={() => void confirmPathBuy()}
        onConfirmRequirements={() => void confirmRequirements()}
        onConfirmStyle={() => void confirmStyle()}
        onRequestChanges={() => void sendUserMessage("手机端打不开，请继续修改")}
        onCompleteAcceptance={() => void completeAcceptance()}
        onConfirmGoLive={() => void confirmGoLive()}
        onPauseProject={() => void pauseProject()}
        onReset={() => void resetDemo()}
      />

      <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden p-3 sm:p-4 lg:p-5">
        <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <CanvasPanel
            state={state}
            onSelectPath={selectPath}
            onSelectTech={selectTech}
            onSelectStyle={selectStyle}
            onToggleAcceptance={(index) =>
              dispatch({ type: "TOGGLE_ACCEPTANCE", index })
            }
            onToggleGoLiveCheck={(index) =>
              dispatch({ type: "TOGGLE_GO_LIVE_CHECK", index })
            }
          />
        </div>
      </main>
    </div>
  );
}
