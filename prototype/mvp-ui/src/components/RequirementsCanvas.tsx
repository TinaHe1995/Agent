import type { RequirementsData } from "../types";
import { CanvasTabs } from "./CanvasTabs";

interface RequirementsCanvasProps {
  requirements: RequirementsData;
  complete: boolean;
  confirmed: boolean;
}

function Section({
  title,
  children,
  filled,
}: {
  title: string;
  children: React.ReactNode;
  filled?: boolean;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        {filled !== undefined &&
          (filled ? (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
              已填写
            </span>
          ) : (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
              待补充
            </span>
          ))}
      </div>
      <div className="text-sm leading-6 text-slate-700">{children}</div>
    </section>
  );
}

function computeProgress(requirements: RequirementsData, complete: boolean) {
  if (complete) return 100;
  const fields = [
    requirements.goal,
    requirements.users,
    requirements.p0Features.length > 0,
    requirements.acceptance.length > 0,
    requirements.outOfScope.length > 0,
    requirements.timeline,
  ];
  return Math.round((fields.filter(Boolean).length / fields.length) * 100);
}

function StageHeader({
  title,
  subtitle,
  accent,
}: {
  title: string;
  subtitle: string;
  accent: "indigo" | "orange" | "violet";
}) {
  const colors = {
    indigo: "border-indigo-100 from-indigo-50 text-indigo-600",
    orange: "border-orange-100 from-orange-50 text-orange-600",
    violet: "border-violet-100 from-violet-50 text-violet-600",
  };
  return (
    <div className={`rounded-xl border bg-gradient-to-r to-white p-4 ${colors[accent].split(" ")[0]} ${colors[accent].split(" ")[1]}`}>
      <div className={`text-xs font-medium uppercase tracking-wide ${colors[accent].split(" ")[2]}`}>
        {subtitle}
      </div>
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
    </div>
  );
}

export function RequirementsCanvas({
  requirements,
  complete,
  confirmed,
}: RequirementsCanvasProps) {
  const progress = computeProgress(requirements, complete);

  const header = (
    <div className="space-y-3">
      <StageHeader
        subtitle="阶段 1 / 做什么"
        title={complete ? "请确认需求文档" : "需求摘要（实时更新）"}
        accent="indigo"
      />
      <div className="flex items-center justify-between rounded-xl border border-indigo-100 bg-indigo-50/50 px-4 py-3">
        <span className="text-sm text-slate-600">需求完成度</span>
        <span className="text-xl font-bold text-indigo-600">{progress}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );

  const tabs = complete
    ? [
        {
          id: "overview",
          label: "文档概览",
          badge: confirmed ? "已确认" : "待确认",
          content: (
            <div className="space-y-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-sm font-semibold text-slate-900">需求文档 v1.0</div>
                <div className="mt-1 text-xs text-slate-500">
                  {confirmed ? "已锁定，作为后续开发依据" : "草案，等待你确认"}
                </div>
              </div>
              <Section title="一句话目标" filled>
                {requirements.goal}
              </Section>
              <Section title="给谁用" filled>
                {requirements.users}
              </Section>
            </div>
          ),
        },
        {
          id: "features",
          label: "功能列表",
          content: (
            <Section title="功能列表" filled>
              <div className="space-y-3">
                <div>
                  <div className="mb-1 text-xs font-medium text-rose-600">P0 必须有</div>
                  <ul className="list-disc space-y-1 pl-5">
                    {requirements.p0Features.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                {requirements.p1Features.length > 0 && (
                  <div>
                    <div className="mb-1 text-xs font-medium text-amber-600">P1 最好有</div>
                    <ul className="list-disc space-y-1 pl-5">
                      {requirements.p1Features.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Section>
          ),
        },
        {
          id: "acceptance",
          label: "验收标准",
          content: (
            <Section title="验收标准" filled>
              <ul className="space-y-2">
                {requirements.acceptance.map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="mt-0.5 text-emerald-500">□</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </Section>
          ),
        },
        {
          id: "scope",
          label: "范围与时间",
          content: (
            <div className="space-y-4">
              <Section title="不做什么" filled>
                <ul className="list-disc space-y-1 pl-5">
                  {requirements.outOfScope.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </Section>
              <Section title="时间预期" filled>
                {requirements.timeline}
              </Section>
            </div>
          ),
        },
      ]
    : [
        {
          id: "overview",
          label: "概览",
          content: (
            <div className="grid gap-3 sm:grid-cols-2">
              <Section title="一句话目标" filled={!!requirements.goal}>
                {requirements.goal || "等待你在左侧回答第一个问题…"}
              </Section>
              <Section title="给谁用" filled={!!requirements.users}>
                {requirements.users || "等待补充"}
              </Section>
            </div>
          ),
        },
        {
          id: "features",
          label: "功能",
          content: (
            <Section title="核心功能 P0" filled={requirements.p0Features.length > 0}>
              {requirements.p0Features.length > 0 ? (
                <ul className="list-disc space-y-1 pl-5">
                  {requirements.p0Features.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                "等待补充"
              )}
            </Section>
          ),
        },
        {
          id: "acceptance",
          label: "验收",
          content: (
            <Section title="验收标准" filled={requirements.acceptance.length > 0}>
              {requirements.acceptance.length > 0 ? (
                <ul className="list-disc space-y-1 pl-5">
                  {requirements.acceptance.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                "等待补充"
              )}
            </Section>
          ),
        },
        {
          id: "scope",
          label: "范围",
          badge: requirements.outOfScope.length > 0 ? "已填" : undefined,
          content: (
            <div className="space-y-4">
              <Section title="不做什么" filled={requirements.outOfScope.length > 0}>
                {requirements.outOfScope.length > 0
                  ? (
                      <ul className="list-disc space-y-1 pl-5">
                        {requirements.outOfScope.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    )
                  : "等待补充"}
              </Section>
              <Section title="时间预期" filled={!!requirements.timeline}>
                {requirements.timeline || "等待补充"}
              </Section>
            </div>
          ),
        },
      ];

  return <CanvasTabs header={header} tabs={tabs} />;
}
