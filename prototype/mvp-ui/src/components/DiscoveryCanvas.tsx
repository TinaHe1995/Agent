import { CanvasTabs } from "./CanvasTabs";
import type { PathChoice } from "../types";

const PATH_OPTIONS = [
  {
    id: "saas" as const,
    name: "买现成 SaaS",
    summary: "最快上线，定制空间小",
    cost: "约 ¥3k/年",
    time: "1 天内",
    fit: "需求标准、追求速度",
  },
  {
    id: "low_code" as const,
    name: "低代码搭建",
    summary: "较快上线，有一定灵活性",
    cost: "约 ¥1k/年",
    time: "3 天左右",
    fit: "需求较简单、可自己调整",
  },
  {
    id: "self_build" as const,
    name: "自研开发",
    summary: "最灵活，周期较长",
    cost: "开发成本较高",
    time: "2～4 周首版",
    fit: "需求特殊、需深度定制",
    recommended: true,
  },
];

interface DiscoveryCanvasProps {
  discoveryBrief: string;
  pathChoice: PathChoice;
  onSelectPath: (choice: PathChoice) => void;
}

export function DiscoveryCanvas({
  discoveryBrief,
  pathChoice,
  onSelectPath,
}: DiscoveryCanvasProps) {
  const tabs = [
    {
      id: "compare",
      label: "方案对比",
      content: (
        <div className="grid gap-3 lg:grid-cols-3">
          {PATH_OPTIONS.map((option) => {
            const selected = pathChoice === option.id;
            return (
              <button
                key={option.id}
                type="button"
                onClick={() => onSelectPath(option.id)}
                className={[
                  "rounded-2xl border p-4 text-left transition",
                  selected
                    ? "border-indigo-400 bg-indigo-50 ring-2 ring-indigo-200"
                    : "border-slate-200 bg-white hover:border-indigo-200",
                ].join(" ")}
              >
                <div className="mb-2 flex items-center justify-between gap-2">
                  <div className="font-semibold text-slate-900">{option.name}</div>
                  {option.recommended && (
                    <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-medium text-indigo-700">
                      推荐
                    </span>
                  )}
                </div>
                <p className="mb-3 text-sm text-slate-600">{option.summary}</p>
                <dl className="space-y-1 text-xs text-slate-500">
                  <div className="flex justify-between gap-2">
                    <dt>费用</dt>
                    <dd className="text-slate-700">{option.cost}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt>周期</dt>
                    <dd className="text-slate-700">{option.time}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt>适合</dt>
                    <dd className="text-right text-slate-700">{option.fit}</dd>
                  </div>
                </dl>
              </button>
            );
          })}
        </div>
      ),
    },
    {
      id: "context",
      label: "你的情况",
      badge: discoveryBrief ? "已记录" : undefined,
      content: (
        <div className="rounded-xl border border-slate-200 bg-slate-50/40 p-4 text-sm leading-6 text-slate-700">
          {discoveryBrief || "在左侧简单描述你想解决的问题，Agent 会帮你更新这里的内容。"}
        </div>
      ),
    },
  ];

  return <CanvasTabs tabs={tabs} />;
}

export function BuyPathCanvas({ pathChoice }: { pathChoice: PathChoice }) {
  const label =
    pathChoice === "saas" ? "买现成 SaaS" : pathChoice === "low_code" ? "低代码搭建" : "外部方案";

  const tabs = [
    {
      id: "guide",
      label: "实施建议",
      content: (
        <div className="space-y-4 text-sm text-slate-700">
          <p>
            你选择了 <strong>{label}</strong>。对于这个请假登记场景，通常不需要从零开发。
          </p>
          <ul className="list-disc space-y-2 pl-5">
            <li>可优先考虑：飞书审批、钉钉审批、腾讯文档收集表</li>
            <li>若只需导出 Excel，很多表单工具已足够</li>
            <li>如后续需求变复杂，仍可回来选择自研</li>
          </ul>
        </div>
      ),
    },
    {
      id: "next",
      label: "下一步",
      content: (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
          本次原型体验在此结束。完整版可继续提供开通步骤、产品链接与对比清单导出。
        </div>
      ),
    },
  ];

  return <CanvasTabs tabs={tabs} />;
}
