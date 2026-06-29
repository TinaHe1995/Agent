import type { AppState } from "../types";
import { DiscoveryCanvas } from "./DiscoveryCanvas";
import { SaasOnboardingCanvas } from "./SaasOnboardingCanvas";
import { PreviewCanvas } from "./PreviewCanvas";
import { ReleaseCanvas } from "./ReleaseCanvas";
import { RequirementsCanvas } from "./RequirementsCanvas";
import { StyleCanvas } from "./StyleCanvas";

interface CanvasPanelProps {
  state: AppState;
  onSelectPath: (choice: AppState["pathChoice"]) => void;
  onSelectTech: (id: AppState["selectedTechId"]) => void;
  onSelectStyle: (id: "A" | "B") => void;
  onToggleAcceptance: (index: number) => void;
  onToggleGoLiveCheck: (index: number) => void;
}

export function CanvasPanel({
  state,
  onSelectPath,
  onSelectTech,
  onSelectStyle,
  onToggleAcceptance,
  onToggleGoLiveCheck,
}: CanvasPanelProps) {
  const panelClass = "h-full min-h-0 p-3 sm:p-4";

  if (state.pathEndedBuy) {
    return (
      <div className={panelClass}>
        <SaasOnboardingCanvas
          pathChoice={state.pathChoice}
          discoveryBrief={state.discoveryBrief}
        />
      </div>
    );
  }

  if (state.stage === 0) {
    return (
      <div className={panelClass}>
        <DiscoveryCanvas
          discoveryBrief={state.discoveryBrief}
          pathChoice={state.pathChoice}
          onSelectPath={onSelectPath}
        />
      </div>
    );
  }

  if (state.stage === 1) {
    return (
      <div className={panelClass}>
        <RequirementsCanvas
          requirements={state.requirements}
          complete={state.requirementsComplete}
          confirmed={state.requirementsConfirmed}
        />
      </div>
    );
  }

  if (state.stage === 2) {
    return (
      <div className={panelClass}>
        <StyleCanvas
          selectedTechId={state.selectedTechId}
          selectedStyleId={state.selectedStyleId}
          styleVersion={state.styleVersion}
          styleWarmth={state.styleWarmth}
          styleButtonSize={state.styleButtonSize}
          onSelectTech={onSelectTech}
          onSelectStyle={onSelectStyle}
        />
      </div>
    );
  }

  if (state.stage === 3) {
    return (
      <div className={panelClass}>
        <PreviewCanvas
          requirements={state.requirements}
          buildProgress={state.buildProgress}
          buildDone={state.buildDone}
          acceptanceChecks={state.acceptanceChecks}
          styleWarmth={state.styleWarmth}
          onToggleAcceptance={onToggleAcceptance}
        />
      </div>
    );
  }

  return (
    <div className={panelClass}>
      <ReleaseCanvas
        stagingProgress={state.stagingProgress}
        stagingReady={state.stagingReady}
        goLiveChecks={state.goLiveChecks}
        onToggleGoLiveCheck={onToggleGoLiveCheck}
        projectCompleted={state.projectCompleted}
      />
    </div>
  );
}
