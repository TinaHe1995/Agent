import type { RequirementsData } from "../types";

interface PreviewCanvasProps {
  requirements: RequirementsData;
  buildProgress: number;
  buildDone: boolean;
  projectCompleted: boolean;
  acceptanceChecks: [boolean, boolean, boolean];
  styleWarmth: number;
  onToggleAcceptance: (index: number) => void;
}

const BUILD_STEPS = [
  { label: "已理解你的需求", threshold: 10 },
  { label: "正在制作页面", threshold: 45 },
  { label: "准备试用链接", threshold: 85 },
];

function InteractivePreview({
  warmth,
  goal,
}: {
  warmth: number;
  goal: string;
}) {
  const isWarm = warmth > 55;
  const primary = isWarm ? "#ea580c" : "#2563eb";

  return (
    <div className="rounded-2xl border bg-white p-4 shadow-sm" style={{ borderColor: isWarm ? "#fed7aa" : "#dbeafe" }}>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-slate-900">可交互预览</div>
          <div className="text-xs text-slate-500">你可以直接点击、输入体验</div>
        </div>
        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
          预览环境
        </span>
      </div>

      <div className="rounded-xl border bg-slate-50 p-4" style={{ borderColor: isWarm ? "#ffedd5" : "#e2e8f0" }}>
        <div className="mb-3 text-sm font-medium text-slate-800">
          {goal.includes("请假") ? "请假登记系统" : "项目预览"}
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="block text-xs text-slate-600">
            姓名
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              defaultValue="张三"
            />
          </label>
          <label className="block text-xs text-slate-600">
            部门
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              defaultValue="行政部"
            />
          </label>
          <label className="block text-xs text-slate-600">
            日期
            <input
              type="date"
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
            />
          </label>
          <label className="block text-xs text-slate-600">
            事由
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              defaultValue="个人事务"
            />
          </label>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-xl px-4 py-2 text-sm font-medium text-white"
            style={{ background: primary }}
          >
            提交请假
          </button>
          <button
            type="button"
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700"
          >
            导出 Excel
          </button>
        </div>
      </div>
    </div>
  );
}

export function PreviewCanvas({
  requirements,
  buildProgress,
  buildDone,
  projectCompleted,
  acceptanceChecks,
  styleWarmth,
  onToggleAcceptance,
}: PreviewCanvasProps) {
  const acceptanceItems = requirements.acceptance.length
    ? requirements.acceptance
    : [
        "核心功能是否可用",
        "页面是否看得懂",
        "你是否愿意把这个链接发给别人试用",
      ];

  if (projectCompleted) {
    return (
      <div className="space-y-4">
        <div className="rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-white p-6 text-center">
          <div className="text-3xl">🎉</div>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">MVP 体验完成</h2>
          <p className="mt-2 text-sm text-slate-600">
            你已经走完「做什么 → 长什么样 → 做出来试试」三阶段。
            <br />
            完整版将在此后增加：测试环境部署 → 你决定是否上线。
          </p>
        </div>
        <InteractivePreview warmth={styleWarmth} goal={requirements.goal} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-violet-100 bg-gradient-to-r from-violet-50 to-white p-5">
        <div className="text-xs font-medium uppercase tracking-wide text-violet-600">
          阶段 3 / 做出来试试
        </div>
        <h2 className="text-lg font-semibold text-slate-900">
          {buildDone ? "请试用并验收" : "正在为你制作第一版"}
        </h2>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-white">
          <div
            className="h-full rounded-full bg-violet-500 transition-all duration-700"
            style={{ width: `${buildProgress}%` }}
          />
        </div>
        <div className="mt-2 text-sm text-slate-600">总进度 {buildProgress}%</div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {BUILD_STEPS.map((step) => {
          const done = buildProgress >= step.threshold;
          const active = !done && buildProgress >= step.threshold - 20;
          return (
            <div
              key={step.label}
              className={[
                "rounded-xl border p-4 text-sm",
                done
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : active
                    ? "border-violet-200 bg-violet-50 text-violet-800"
                    : "border-slate-200 bg-white text-slate-500",
              ].join(" ")}
            >
              <div className="mb-1 font-medium">{done ? "✅" : active ? "🔄" : "⏳"} {step.label}</div>
            </div>
          );
        })}
      </div>

      {buildDone ? (
        <>
          <InteractivePreview warmth={styleWarmth} goal={requirements.goal} />
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 text-sm font-semibold text-slate-900">验收清单（对照需求文档）</div>
            <div className="space-y-3">
              {acceptanceItems.slice(0, 3).map((item, index) => (
                <label
                  key={item}
                  className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"
                >
                  <input
                    type="checkbox"
                    checked={acceptanceChecks[index]}
                    onChange={() => onToggleAcceptance(index)}
                    className="mt-1"
                  />
                  <div>
                    <div className="text-sm font-medium text-slate-800">{item}</div>
                    <div className="text-xs text-slate-500">请实际操作后勾选</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
          制作完成后，这里会出现可交互预览和验收清单
        </div>
      )}
    </div>
  );
}
