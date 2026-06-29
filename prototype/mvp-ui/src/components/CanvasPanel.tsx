import type { AppState } from "../types";
import { PreviewCanvas } from "./PreviewCanvas";
import { RequirementsCanvas } from "./RequirementsCanvas";
import { StyleCanvas } from "./StyleCanvas";

interface CanvasPanelProps {
  state: AppState;
  onSelectStyle: (id: "A" | "B") => void;
  onToggleAcceptance: (index: number) => void;
}

export function CanvasPanel({ state, onSelectStyle, onToggleAcceptance }: CanvasPanelProps) {
  const panelClass = "h-full min-h-0 p-3 sm:p-4";

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
          selectedStyleId={state.selectedStyleId}
          styleVersion={state.styleVersion}
          styleWarmth={state.styleWarmth}
          styleButtonSize={state.styleButtonSize}
          onSelectStyle={onSelectStyle}
        />
      </div>
    );
  }

  return (
    <div className={panelClass}>
      <PreviewCanvas
        requirements={state.requirements}
        buildProgress={state.buildProgress}
        buildDone={state.buildDone}
        projectCompleted={state.projectCompleted}
        acceptanceChecks={state.acceptanceChecks}
        styleWarmth={state.styleWarmth}
        onToggleAcceptance={onToggleAcceptance}
      />
    </div>
  );
}
