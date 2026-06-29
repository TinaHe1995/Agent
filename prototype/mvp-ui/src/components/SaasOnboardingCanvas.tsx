import { useState } from "react";
import type { PathChoice } from "../types";
import { CanvasTabs } from "./CanvasTabs";

const SAAS_PRODUCTS = [
  {
    id: "feishu",
    name: "飞书审批",
    tag: "推荐",
    time: "约 15 分钟",
    summary: "模板多、导出方便，适合已用飞书的公司",
    link: "https://www.feishu.cn/approval",
  },
  {
    id: "dingtalk",
    name: "钉钉审批",
    tag: null,
    time: "约 20 分钟",
    summary: "与钉钉通讯录打通，适合制造业、连锁门店",
    link: "https://www.dingtalk.com",
  },
  {
    id: "tencent",
    name: "腾讯文档收集表",
    tag: null,
    time: "约 10 分钟",
    summary: "零门槛，适合临时收集、轻量登记",
    link: "https://docs.qq.com",
  },
];

const ADMIN_STEPS = [
  {
    id: "pick",
    title: "选定产品并登录管理后台",
    detail: "建议优先飞书审批；若公司已在用钉钉，选钉钉更省事。",
  },
  {
    id: "template",
    title: "复制「请假登记」模板并发布",
    detail: "字段保留：姓名、部门、日期、事由；开启 Excel 导出。",
  },
  {
    id: "invite",
    title: "邀请全员或指定部门",
    detail: "把审批入口发到公司群，或写入员工手册链接。",
  },
  {
    id: "test",
    title: "自己先提交一条测试请假",
    detail: "确认能收到通知、能导出，再让员工正式使用。",
  },
];

const EMPLOYEE_STEPS = [
  { n: 1, title: "打开链接", body: "从群公告或人事通知里点开「请假登记」" },
  { n: 2, title: "填写信息", body: "姓名、部门、日期、事由，一般 1 分钟内完成" },
  { n: 3, title: "提交即可", body: "无需催办行政，数据会自动汇总" },
];

interface SaasOnboardingCanvasProps {
  pathChoice: PathChoice;
  discoveryBrief?: string;
}

export function SaasOnboardingCanvas({
  pathChoice,
  discoveryBrief,
}: SaasOnboardingCanvasProps) {
  const isLowCode = pathChoice === "low_code";
  const [selectedProduct, setSelectedProduct] = useState("feishu");
  const [adminDone, setAdminDone] = useState<Record<string, boolean>>({});
  const [employeeStep, setEmployeeStep] = useState(1);

  const adminCount = ADMIN_STEPS.filter((s) => adminDone[s.id]).length;
  const product = SAAS_PRODUCTS.find((p) => p.id === selectedProduct) ?? SAAS_PRODUCTS[0];

  const welcomeTab = {
    id: "welcome",
    label: "欢迎引导",
    content: (
      <div className="space-y-5">
        <div className="rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 p-6 text-white shadow-md">
          <div className="text-xs font-medium uppercase tracking-wide text-indigo-200">
            {isLowCode ? "低代码路线" : "SaaS 路线"}
          </div>
          <h2 className="mt-2 text-xl font-semibold">你的请假方案已就绪</h2>
          <p className="mt-2 text-sm leading-6 text-indigo-100">
            不用写代码，今天就能用起来。管理员按右侧步骤开通，员工打开链接即可登记。
          </p>
          {discoveryBrief && (
            <div className="mt-4 rounded-xl bg-white/10 px-4 py-3 text-sm text-indigo-50">
              <span className="font-medium text-white">你的情况：</span>
              {discoveryBrief.split("\n").slice(-1)[0]}
            </div>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          {[
            { icon: "1", title: "管理员开通", desc: "约 15～20 分钟" },
            { icon: "2", title: "发给员工", desc: "分享引导页链接" },
            { icon: "3", title: "试跑一条", desc: "确认能导出" },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-center"
            >
              <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
                {item.icon}
              </div>
              <div className="text-sm font-medium text-slate-900">{item.title}</div>
              <div className="mt-1 text-xs text-slate-500">{item.desc}</div>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {isLowCode
            ? "低代码方案可在可视化后台自己改字段；若后续需求变复杂，仍可回来选择自研。"
            : "SaaS 方案适合标准请假场景。若以后要深度定制，可随时在对话里说「改走自研」。"}
        </div>
      </div>
    ),
  };

  const setupTab = {
    id: "setup",
    label: "开通步骤",
    badge: `${adminCount}/${ADMIN_STEPS.length}`,
    content: (
      <div className="space-y-5">
        <div>
          <div className="mb-2 text-sm font-medium text-slate-900">先选一个产品</div>
          <div className="grid gap-2 sm:grid-cols-3">
            {SAAS_PRODUCTS.map((p) => {
              const active = selectedProduct === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setSelectedProduct(p.id)}
                  className={[
                    "rounded-xl border p-3 text-left transition",
                    active
                      ? "border-indigo-400 bg-indigo-50 ring-2 ring-indigo-200"
                      : "border-slate-200 bg-white hover:border-indigo-200",
                  ].join(" ")}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900">{p.name}</span>
                    {p.tag && (
                      <span className="rounded-full bg-indigo-100 px-1.5 py-0.5 text-[10px] text-indigo-700">
                        {p.tag}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-slate-500">{p.time}</p>
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <div>
            <div className="text-sm font-medium text-slate-900">已选：{product.name}</div>
            <div className="text-xs text-slate-500">{product.summary}</div>
          </div>
          <a
            href={product.link}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-medium text-white hover:bg-indigo-700"
          >
            打开官网
          </a>
        </div>

        <div className="space-y-2">
          {ADMIN_STEPS.map((step, index) => {
            const done = adminDone[step.id];
            return (
              <label
                key={step.id}
                className={[
                  "flex cursor-pointer gap-3 rounded-xl border p-4 transition",
                  done ? "border-emerald-200 bg-emerald-50/50" : "border-slate-200 hover:bg-slate-50",
                ].join(" ")}
              >
                <input
                  type="checkbox"
                  checked={done}
                  onChange={() =>
                    setAdminDone((prev) => ({ ...prev, [step.id]: !prev[step.id] }))
                  }
                  className="mt-1"
                />
                <div>
                  <div className="text-sm font-medium text-slate-900">
                    {index + 1}. {step.title}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">{step.detail}</div>
                </div>
              </label>
            );
          })}
        </div>
      </div>
    ),
  };

  const employeeTab = {
    id: "employee",
    label: "员工打开页",
    badge: `第 ${employeeStep} 步`,
    content: (
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-3">
          <p className="text-sm text-slate-600">
            员工第一次打开网页时，可展示这样的引导（3 步，约 30 秒看完）：
          </p>
          {EMPLOYEE_STEPS.map((step) => {
            const active = employeeStep === step.n;
            return (
              <button
                key={step.n}
                type="button"
                onClick={() => setEmployeeStep(step.n)}
                className={[
                  "w-full rounded-xl border p-4 text-left transition",
                  active
                    ? "border-indigo-400 bg-indigo-50 ring-2 ring-indigo-200"
                    : "border-slate-200 bg-white hover:border-indigo-200",
                ].join(" ")}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={[
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                      active ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600",
                    ].join(" ")}
                  >
                    {step.n}
                  </span>
                  <div>
                    <div className="text-sm font-medium text-slate-900">{step.title}</div>
                    <div className="text-xs text-slate-500">{step.body}</div>
                  </div>
                </div>
              </button>
            );
          })}
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-xs text-slate-500">
            完整版可生成「员工引导链接」或二维码，发到公司群一键打开。
          </div>
        </div>

        <EmployeePageMock step={employeeStep} productName={product.name} />
      </div>
    ),
  };

  const handoffTab = {
    id: "handoff",
    label: "发给同事",
    disabled: adminCount < ADMIN_STEPS.length,
    badge: adminCount >= ADMIN_STEPS.length ? "可发送" : "先完成开通",
    content: (
      <div className="space-y-4">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          开通步骤已完成。把下面文案复制到公司群即可。
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 font-mono text-xs leading-6 text-slate-700">
          【请假登记上线啦】
          <br />
          请大家用 {product.name} 登记请假，链接见群公告。
          <br />
          操作很简单：打开 → 填信息 → 提交，1 分钟搞定。
          <br />
          有问题找行政 @{`{你的名字}`}
        </div>
        <button
          type="button"
          className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
          onClick={() => navigator.clipboard?.writeText(`【请假登记上线啦】请大家用 ${product.name} 登记请假…`)}
        >
          复制群公告文案
        </button>
      </div>
    ),
  };

  const tabs = isLowCode
    ? [welcomeTab, setupTab, employeeTab]
    : [welcomeTab, setupTab, employeeTab, handoffTab];

  return <CanvasTabs tabs={tabs} />;
}

function EmployeePageMock({ step, productName }: { step: number; productName: string }) {
  return (
    <div className="mx-auto w-full max-w-[280px]">
      <div className="rounded-[2rem] border-4 border-slate-800 bg-slate-800 p-2 shadow-xl">
        <div className="overflow-hidden rounded-[1.4rem] bg-white">
          <div className="bg-slate-100 px-4 py-2 text-center text-[10px] text-slate-500">
            {productName} · 请假登记
          </div>

          <div className="relative min-h-[340px] p-4">
            {step === 1 && (
              <div className="absolute inset-x-4 top-3 rounded-lg border-2 border-dashed border-indigo-400 bg-indigo-50/90 px-3 py-2 text-center text-xs font-medium text-indigo-800">
                👆 从群公告点这里进入
              </div>
            )}

            <div className="mt-10 space-y-3">
              <div className="text-base font-semibold text-slate-900">请假登记</div>
              {["姓名", "部门", "日期", "事由"].map((label, i) => (
                <div
                  key={label}
                  className={[
                    "relative rounded-lg border px-3 py-2",
                    step === 2 && i < 2
                      ? "border-indigo-400 bg-indigo-50 ring-2 ring-indigo-200"
                      : "border-slate-200 bg-slate-50",
                  ].join(" ")}
                >
                  <div className="text-[10px] text-slate-500">{label}</div>
                  <div className="h-4 text-xs text-slate-400">
                    {label === "姓名" ? "张三" : label === "部门" ? "行政部" : "请填写"}
                  </div>
                  {step === 2 && i === 0 && (
                    <div className="absolute -right-1 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-[10px] font-bold text-white">
                      2
                    </div>
                  )}
                </div>
              ))}
            </div>

            <button
              type="button"
              className={[
                "mt-4 w-full rounded-xl py-2.5 text-sm font-medium text-white",
                step === 3 ? "bg-emerald-500 ring-4 ring-emerald-200" : "bg-indigo-600",
              ].join(" ")}
            >
              {step === 3 ? "✓ 提交成功" : "提交请假"}
            </button>

            {step === 3 && (
              <div className="mt-3 rounded-lg bg-emerald-50 px-3 py-2 text-center text-xs text-emerald-800">
                已提交，行政可在后台导出
              </div>
            )}
          </div>
        </div>
      </div>
      <p className="mt-3 text-center text-xs text-slate-400">员工手机打开网页后的引导预览</p>
    </div>
  );
}
