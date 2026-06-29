import { CanvasTabs } from "./CanvasTabs";

interface ReleaseCanvasProps {
  stagingProgress: number;
  stagingReady: boolean;
  goLiveChecks: [boolean, boolean, boolean];
  onToggleGoLiveCheck: (index: number) => void;
  projectCompleted: boolean;
}

const GO_LIVE_ITEMS = [
  "我已让同事在测试环境试用",
  "我确认数据会自动备份",
  "我了解出问题可以回退",
];

export function ReleaseCanvas({
  stagingProgress,
  stagingReady,
  goLiveChecks,
  onToggleGoLiveCheck,
  projectCompleted,
}: ReleaseCanvasProps) {
  if (projectCompleted) {
    return (
      <CanvasTabs
        tabs={[
          {
            id: "live",
            label: "正式地址",
            content: (
              <div className="space-y-4">
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                  已上线正式环境
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-xs text-slate-500">正式地址</div>
                  <div className="mt-1 font-medium text-indigo-700">
                    https://leave-app.example.com
                  </div>
                </div>
              </div>
            ),
          },
          {
            id: "handover",
            label: "交付物",
            content: (
              <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
                <li>需求文档（已锁定版本）</li>
                <li>应用 v1.0</li>
                <li>测试记录与上线检查单</li>
              </ul>
            ),
          },
        ]}
      />
    );
  }

  const tabs = [
    {
      id: "staging",
      label: "测试环境",
      badge: stagingReady ? "就绪" : `${stagingProgress}%`,
      content: stagingReady ? (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs text-slate-500">测试环境链接</div>
            <div className="mt-1 break-all font-medium text-indigo-700">
              https://test.leave-app.example.com
            </div>
          </div>
          <p className="text-sm text-slate-600">
            建议先让 2～3 位同事试用，确认无问题后再决定是否上线。
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-indigo-500 transition-all duration-700"
              style={{ width: `${stagingProgress}%` }}
            />
          </div>
          <p className="text-sm text-slate-500">正在部署测试环境…</p>
        </div>
      ),
    },
    {
      id: "checklist",
      label: "上线检查",
      disabled: !stagingReady,
      badge: stagingReady
        ? `${goLiveChecks.filter(Boolean).length}/3`
        : undefined,
      content: stagingReady ? (
        <div className="space-y-3">
          {GO_LIVE_ITEMS.map((item, index) => (
            <label
              key={item}
              className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"
            >
              <input
                type="checkbox"
                checked={goLiveChecks[index]}
                onChange={() => onToggleGoLiveCheck(index)}
                className="mt-1"
              />
              <span className="text-sm text-slate-800">{item}</span>
            </label>
          ))}
        </div>
      ) : (
        <div className="flex min-h-[200px] items-center justify-center text-sm text-slate-500">
          测试环境就绪后，可在此勾选上线检查项
        </div>
      ),
    },
    {
      id: "prod",
      label: "正式环境",
      disabled: !stagingReady,
      content: (
        <div className="flex min-h-[200px] items-center justify-center text-sm text-slate-500">
          确认上线后，正式地址会出现在这里
        </div>
      ),
    },
  ];

  return <CanvasTabs tabs={tabs} />;
}
