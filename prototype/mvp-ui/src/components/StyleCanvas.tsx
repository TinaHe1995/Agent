import { STYLE_OPTIONS } from "../mockAgent";
import { CanvasTabs } from "./CanvasTabs";

interface StyleCanvasProps {
  selectedStyleId: "A" | "B" | null;
  styleVersion: number;
  styleWarmth: number;
  styleButtonSize: number;
  onSelectStyle: (id: "A" | "B") => void;
}

function PreviewMock({
  styleId,
  warmth,
  buttonSize,
}: {
  styleId: "A" | "B";
  warmth: number;
  buttonSize: number;
}) {
  const isWarm = styleId === "B" || warmth > 55;
  const primary = isWarm ? "#ea580c" : "#2563eb";
  const bg = isWarm ? "#fff7ed" : "#f8fafc";
  const card = "#ffffff";
  const buttonPaddingY = 8 + Math.round((buttonSize / 100) * 10);
  const buttonPaddingX = 16 + Math.round((buttonSize / 100) * 12);
  const buttonFontSize = 12 + Math.round((buttonSize / 100) * 6);

  return (
    <div
      className="overflow-hidden rounded-2xl border shadow-inner"
      style={{ background: bg, borderColor: isWarm ? "#fed7aa" : "#dbeafe" }}
    >
      <div className="border-b px-4 py-2 text-xs text-slate-500" style={{ background: card }}>
        关键页面预览 · 员工请假页
      </div>
      <div className="flex min-h-[360px] items-center justify-center p-6">
        <div className="w-full max-w-sm rounded-2xl border bg-white p-5 shadow-sm" style={{ borderColor: isWarm ? "#ffedd5" : "#e2e8f0" }}>
          <div className="mb-1 text-lg font-semibold" style={{ color: isWarm ? "#9a3412" : "#1e3a8a" }}>
            请假登记
          </div>
          <div className="mb-4 text-xs text-slate-500">请填写以下信息</div>
          <div className="space-y-3">
            {["姓名", "部门", "日期", "事由"].map((label) => (
              <div key={label}>
                <div className="mb-1 text-xs text-slate-600">{label}</div>
                <div className="h-9 rounded-lg border bg-slate-50" style={{ borderColor: isWarm ? "#fdba74" : "#cbd5e1" }} />
              </div>
            ))}
          </div>
          <button
            type="button"
            className="mt-4 w-full rounded-xl font-medium text-white"
            style={{
              background: primary,
              padding: `${buttonPaddingY}px ${buttonPaddingX}px`,
              fontSize: `${buttonFontSize}px`,
            }}
          >
            提交请假
          </button>
        </div>
      </div>
    </div>
  );
}

export function StyleCanvas({
  selectedStyleId,
  styleVersion,
  styleWarmth,
  styleButtonSize,
  onSelectStyle,
}: StyleCanvasProps) {
  const activeStyle = selectedStyleId ?? "B";

  const header = (
    <div className="rounded-xl border border-orange-100 bg-gradient-to-r from-orange-50 to-white p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-orange-600">
        界面风格
      </div>
      <h2 className="text-lg font-semibold text-slate-900">选择界面风格</h2>
      <p className="mt-1 text-sm text-slate-600">
        技术方案已由 Agent 自动选择（网页应用）。在「选风格」Tab 中挑选，在「预览」Tab 中查看效果。
      </p>
    </div>
  );

  const tabs = [
    {
      id: "pick",
      label: "选风格",
      badge: selectedStyleId ? `已选 ${selectedStyleId}` : undefined,
      content: (
        <div className="grid gap-3 sm:grid-cols-2">
          {STYLE_OPTIONS.map((style) => {
            const selected = selectedStyleId === style.id;
            return (
              <button
                key={style.id}
                type="button"
                onClick={() => onSelectStyle(style.id)}
                className={[
                  "rounded-2xl border p-4 text-left transition",
                  selected
                    ? "border-orange-400 bg-orange-50 ring-2 ring-orange-200"
                    : "border-slate-200 bg-white hover:border-orange-200 hover:bg-orange-50/40",
                ].join(" ")}
              >
                <div className="mb-2 flex items-center justify-between">
                  <div className="font-semibold text-slate-900">
                    风格 {style.id} · {style.name}
                  </div>
                  {style.recommended && (
                    <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-medium text-orange-700">
                      推荐
                    </span>
                  )}
                </div>
                <p className="mb-3 text-sm text-slate-600">{style.description}</p>
                <div className="flex gap-2">
                  {style.colors.map((color) => (
                    <div
                      key={color}
                      className="h-6 w-6 rounded-full border border-white shadow"
                      style={{ background: color }}
                    />
                  ))}
                </div>
              </button>
            );
          })}
        </div>
      ),
    },
    {
      id: "preview",
      label: "页面预览",
      badge: `v${styleVersion}`,
      content: (
        <div>
          <PreviewMock
            styleId={activeStyle}
            warmth={styleWarmth}
            buttonSize={styleButtonSize}
          />
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
            <span className="rounded-full bg-slate-100 px-2 py-1">桌面预览</span>
            <span className="rounded-full bg-slate-100 px-2 py-1">手机预览</span>
            <span className="rounded-full bg-slate-100 px-2 py-1">可在左侧聊天继续修改</span>
          </div>
        </div>
      ),
    },
  ];

  return <CanvasTabs header={header} tabs={tabs} />;
}
