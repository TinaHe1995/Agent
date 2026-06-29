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
  if (state.stage === 1) {
    return (
      <RequirementsCanvas
        requirements={state.requirements}
        complete={state.requirementsComplete}
        confirmed={state.requirementsConfirmed}
      />
    );
  }

  if (state.stage === 2) {
    return (
      <StyleCanvas
        selectedStyleId={state.selectedStyleId}
        styleVersion={state.styleVersion}
        styleWarmth={state.styleWarmth}
        styleButtonSize={state.styleButtonSize}
        onSelectStyle={onSelectStyle}
      />
    );
  }

  return (
    <PreviewCanvas
      requirements={state.requirements}
      buildProgress={state.buildProgress}
      buildDone={state.buildDone}
      projectCompleted={state.projectCompleted}
      acceptanceChecks={state.acceptanceChecks}
      styleWarmth={state.styleWarmth}
      onToggleAcceptance={onToggleAcceptance}
    />
  );
}
