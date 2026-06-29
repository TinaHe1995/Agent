import type { Stage } from "../types";

const STAGES = [
  { id: 1 as Stage, label: "做什么" },
  { id: 2 as Stage, label: "长什么样" },
  { id: 3 as Stage, label: "做出来试试" },
];

interface StageProgressProps {
  currentStage: Stage;
  projectCompleted: boolean;
}

export function StageProgress({ currentStage, projectCompleted }: StageProgressProps) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto">
      {STAGES.map((stage, index) => {
        const active = stage.id === currentStage && !projectCompleted;
        const done = stage.id < currentStage || projectCompleted;
        return (
          <div key={stage.id} className="flex items-center gap-2 shrink-0">
            <div className="flex items-center gap-2">
              <div
                className={[
                  "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold",
                  done
                    ? "bg-emerald-500 text-white"
                    : active
                      ? "bg-indigo-600 text-white ring-4 ring-indigo-100"
                      : "bg-slate-200 text-slate-500",
                ].join(" ")}
              >
                {done ? "✓" : stage.id}
              </div>
              <span
                className={[
                  "text-sm font-medium",
                  active ? "text-indigo-700" : done ? "text-emerald-700" : "text-slate-500",
                ].join(" ")}
              >
                {stage.label}
              </span>
            </div>
            {index < STAGES.length - 1 && (
              <div className={`h-px w-8 sm:w-12 ${done ? "bg-emerald-300" : "bg-slate-200"}`} />
            )}
          </div>
        );
      })}
      {projectCompleted && (
        <span className="ml-2 rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
          体验完成
        </span>
      )}
    </div>
  );
}
