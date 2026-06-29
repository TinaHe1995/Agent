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
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-slate-50/40 p-4">
      <h3 className="mb-2 text-sm font-semibold text-slate-900">{title}</h3>
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

export function RequirementsCanvas({
  requirements,
  complete,
  confirmed,
}: RequirementsCanvasProps) {
  const progress = computeProgress(requirements, complete);

  const tabs = complete
    ? [
        {
          id: "overview",
          label: "文档概览",
          badge: confirmed ? "已确认" : "待确认",
          content: (
            <div className="space-y-4">
              <Section title="一句话目标">{requirements.goal}</Section>
              <Section title="给谁用">{requirements.users}</Section>
            </div>
          ),
        },
        {
          id: "features",
          label: "功能列表",
          content: (
            <Section title="功能列表">
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
            <Section title="验收标准">
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
              <Section title="不做什么">
                <ul className="list-disc space-y-1 pl-5">
                  {requirements.outOfScope.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </Section>
              <Section title="时间预期">{requirements.timeline}</Section>
            </div>
          ),
        },
      ]
    : [
        {
          id: "overview",
          label: "概览",
          badge: progress > 0 && progress < 100 ? `${progress}%` : undefined,
          content: (
            <div className="grid gap-3 sm:grid-cols-2">
              <Section title="一句话目标">
                {requirements.goal || "等待你在左侧回答…"}
              </Section>
              <Section title="给谁用">
                {requirements.users || "等待补充"}
              </Section>
            </div>
          ),
        },
        {
          id: "features",
          label: "功能",
          content: (
            <Section title="核心功能 P0">
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
            <Section title="验收标准">
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
          content: (
            <div className="space-y-4">
              <Section title="不做什么">
                {requirements.outOfScope.length > 0 ? (
                  <ul className="list-disc space-y-1 pl-5">
                    {requirements.outOfScope.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  "等待补充"
                )}
              </Section>
              <Section title="时间预期">
                {requirements.timeline || "等待补充"}
              </Section>
            </div>
          ),
        },
      ];

  return <CanvasTabs tabs={tabs} />;
}
