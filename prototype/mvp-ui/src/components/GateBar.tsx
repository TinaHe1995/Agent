import type { GateType, PathChoice, Stage, TechChoice } from "../types";

interface GateBarProps {
  stage: Stage;
  pendingGate: GateType;
  pathChoice: PathChoice;
  discoveryReady: boolean;
  pathEndedBuy: boolean;
  requirementsComplete: boolean;
  selectedTechId: TechChoice;
  selectedStyleId: "A" | "B" | null;
  buildDone: boolean;
  acceptanceChecks: [boolean, boolean, boolean];
  stagingReady: boolean;
  goLiveChecks: [boolean, boolean, boolean];
  projectCompleted: boolean;
  onConfirmPathSelfBuild: () => void;
  onConfirmPathBuy: () => void;
  onConfirmRequirements: () => void;
  onConfirmStyle: () => void;
  onRequestChanges: () => void;
  onCompleteAcceptance: () => void;
  onConfirmGoLive: () => void;
  onPauseProject: () => void;
  compact?: boolean;
}

export function GateBar({
  stage,
  pendingGate,
  pathChoice,
  discoveryReady,
  pathEndedBuy,
  requirementsComplete,
  selectedTechId,
  selectedStyleId,
  buildDone,
  acceptanceChecks,
  stagingReady,
  goLiveChecks,
  projectCompleted,
  onConfirmPathSelfBuild,
  onConfirmPathBuy,
  onConfirmRequirements,
  onConfirmStyle,
  onRequestChanges,
  onCompleteAcceptance,
  onConfirmGoLive,
  onPauseProject,
  compact = false,
}: GateBarProps) {
  if (projectCompleted && !pathEndedBuy) {
    return (
      <div
        className={[
          "text-sm text-emerald-800",
          compact
            ? "rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2.5"
            : "rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3",
        ].join(" ")}
      >
        项目已上线。可点击上方「重新开始」再体验一遍。
      </div>
    );
  }

  if (pathEndedBuy) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-600">
        已选择外部方案，本次体验结束。
      </div>
    );
  }

  let title = "当前无需拍板，可继续在左侧聊天";
  let primaryLabel: string | null = null;
  let primaryAction: (() => void) | null = null;
  let secondaryLabel: string | null = null;
  let secondaryAction: (() => void) | null = null;
  let disabled = false;

  if (stage === 0 && discoveryReady && pendingGate === "path") {
    if (pathChoice === "self_build") {
      title = "确认按自研路线继续";
      primaryLabel = "确认，开始整理需求";
      primaryAction = onConfirmPathSelfBuild;
      secondaryLabel = "改选其他方案";
      secondaryAction = () => undefined;
    } else if (pathChoice === "saas" || pathChoice === "low_code") {
      title = "确认采用外部方案？";
      primaryLabel = "确认，查看实施建议";
      primaryAction = onConfirmPathBuy;
      secondaryLabel = "改选自研";
      secondaryAction = () => undefined;
    } else {
      title = "请先在右侧选择一种方案";
    }
  }

  if (stage === 1 && requirementsComplete && pendingGate === "requirements") {
    title = "请确认需求文档后继续";
    primaryLabel = "确认需求，继续";
    primaryAction = onConfirmRequirements;
    secondaryLabel = "我还要改";
    secondaryAction = () => undefined;
  }

  if (stage === 2 && pendingGate === "style") {
    title =
      selectedTechId && selectedStyleId
        ? "确认技术路线与界面风格"
        : "请先选择技术路线和界面风格";
    primaryLabel = "确认，开始制作";
    primaryAction = onConfirmStyle;
    disabled = !selectedTechId || !selectedStyleId;
  }

  if (stage === 3 && buildDone && pendingGate === "acceptance") {
    const allChecked = acceptanceChecks.every(Boolean);
    title = allChecked ? "验收通过，进入部署准备" : "请试用后勾选验收清单";
    primaryLabel = "验收通过，继续";
    primaryAction = onCompleteAcceptance;
    secondaryLabel = "还不行，继续改";
    secondaryAction = onRequestChanges;
    disabled = !allChecked;
  }

  if (stage === 4 && stagingReady && pendingGate === "go_live") {
    const allChecked = goLiveChecks.every(Boolean);
    title = allChecked ? "确认上线正式环境" : "请完成上线检查项";
    primaryLabel = "上线正式环境";
    primaryAction = onConfirmGoLive;
    secondaryLabel = "再测试一周";
    secondaryAction = onPauseProject;
    disabled = !allChecked;
  }

  return (
    <div
      className={[
        compact
          ? "rounded-xl border border-slate-200 bg-slate-50 px-3 py-3"
          : "rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm",
      ].join(" ")}
    >
      <div className={`flex flex-col gap-3 ${compact ? "" : "lg:flex-row lg:items-center lg:justify-between"}`}>
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            待你拍板
          </div>
          <div className="text-sm font-medium text-slate-900">{title}</div>
        </div>
        <div className={`flex gap-2 ${compact ? "flex-col" : "flex-wrap"}`}>
          {secondaryLabel && secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction}
              className={[
                "rounded-xl border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50",
                compact ? "w-full px-3 py-2" : "px-4 py-2.5",
              ].join(" ")}
            >
              {secondaryLabel}
            </button>
          )}
          {primaryLabel && primaryAction && (
            <button
              type="button"
              onClick={primaryAction}
              disabled={disabled}
              className={[
                "rounded-xl bg-indigo-600 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300",
                compact ? "w-full px-3 py-2" : "px-4 py-2.5",
              ].join(" ")}
            >
              {primaryLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
