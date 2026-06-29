import type { RequirementsData } from "../types";

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
    <section className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        {filled ? (
          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
            已填写
          </span>
        ) : (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
            待补充
          </span>
        )}
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

export function RequirementsCanvas({
  requirements,
  complete,
  confirmed,
}: RequirementsCanvasProps) {
  const progress = computeProgress(requirements, complete);

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-indigo-100 bg-gradient-to-r from-indigo-50 to-white p-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <div className="text-xs font-medium uppercase tracking-wide text-indigo-600">
              阶段 1 / 做什么
            </div>
            <h2 className="text-lg font-semibold text-slate-900">
              {complete ? "请确认需求文档" : "需求摘要（实时更新）"}
            </h2>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-indigo-600">{progress}%</div>
            <div className="text-xs text-slate-500">完成度</div>
          </div>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-white">
          <div
            className="h-full rounded-full bg-indigo-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {!complete ? (
        <div className="grid gap-3">
          <Section title="一句话目标" filled={!!requirements.goal}>
            {requirements.goal || "等待你在左侧回答第一个问题…"}
          </Section>
          <Section title="给谁用" filled={!!requirements.users}>
            {requirements.users || "等待补充"}
          </Section>
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
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-900">需求文档 v1.0</div>
              <div className="text-xs text-slate-500">
                {confirmed ? "已锁定，作为后续开发依据" : "草案，等待你确认"}
              </div>
            </div>
            {confirmed && (
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
                已确认
              </span>
            )}
          </div>

          <div className="space-y-4">
            <Section title="1. 项目目标" filled>
              {requirements.goal}
            </Section>
            <Section title="2. 用户与场景" filled>
              {requirements.users}
            </Section>
            <Section title="3. 功能列表" filled>
              <div className="space-y-2">
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
            <Section title="4. 验收标准" filled>
              <ul className="space-y-2">
                {requirements.acceptance.map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="mt-0.5 text-emerald-500">□</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </Section>
            <Section title="5. 范围外" filled>
              <ul className="list-disc space-y-1 pl-5">
                {requirements.outOfScope.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Section>
            <Section title="6. 时间预期" filled>
              {requirements.timeline}
            </Section>
          </div>
        </div>
      )}
    </div>
  );
}
