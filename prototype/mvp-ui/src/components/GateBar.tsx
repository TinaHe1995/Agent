import type { GateType } from "../types";

interface GateBarProps {
  stage: number;
  pendingGate: GateType;
  requirementsComplete: boolean;
  selectedStyleId: "A" | "B" | null;
  buildDone: boolean;
  acceptanceChecks: [boolean, boolean, boolean];
  projectCompleted: boolean;
  onConfirmRequirements: () => void;
  onConfirmStyle: () => void;
  onRequestChanges: () => void;
  onCompleteProject: () => void;
}

export function GateBar({
  stage,
  pendingGate,
  requirementsComplete,
  selectedStyleId,
  buildDone,
  acceptanceChecks,
  projectCompleted,
  onConfirmRequirements,
  onConfirmStyle,
  onRequestChanges,
  onCompleteProject,
}: GateBarProps) {
  if (projectCompleted) {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
        你已完成本次 MVP 体验。可以点击右上角「重新开始」再体验一遍。
      </div>
    );
  }

  let title = "当前无需拍板，可继续在左侧聊天";
  let primaryLabel: string | null = null;
  let primaryAction: (() => void) | null = null;
  let secondaryLabel: string | null = null;
  let secondaryAction: (() => void) | null = null;
  let disabled = false;

  if (stage === 1 && requirementsComplete && pendingGate === "requirements") {
    title = "请确认需求文档后继续";
    primaryLabel = "确认需求，继续";
    primaryAction = onConfirmRequirements;
    secondaryLabel = "我还要改";
    secondaryAction = () => undefined;
  }

  if (stage === 2 && pendingGate === "style") {
    title = selectedStyleId
      ? `已选风格 ${selectedStyleId}，确认后开始制作`
      : "请先选择一套风格（推荐风格 B）";
    primaryLabel = "确认风格，开始制作";
    primaryAction = onConfirmStyle;
    disabled = !selectedStyleId;
  }

  if (stage === 3 && buildDone && pendingGate === "acceptance") {
    const allChecked = acceptanceChecks.every(Boolean);
    title = allChecked
      ? "验收通过，可以完成本次体验"
      : "请对照右侧预览，勾选验收清单";
    primaryLabel = "可以了，完成";
    primaryAction = onCompleteProject;
    secondaryLabel = "还不行，继续改";
    secondaryAction = onRequestChanges;
    disabled = !allChecked;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            待你拍板
          </div>
          <div className="text-sm font-medium text-slate-900">{title}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          {secondaryLabel && secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              {secondaryLabel}
            </button>
          )}
          {primaryLabel && primaryAction && (
            <button
              type="button"
              onClick={primaryAction}
              disabled={disabled}
              className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {primaryLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
