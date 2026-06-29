import { useEffect, useState } from "react";

export interface CanvasTab {
  id: string;
  label: string;
  badge?: string;
  disabled?: boolean;
  content: React.ReactNode;
}

interface CanvasTabsProps {
  tabs: CanvasTab[];
  activeTabId?: string;
  onTabChange?: (id: string) => void;
  header?: React.ReactNode;
}

export function CanvasTabs({ tabs, activeTabId, onTabChange, header }: CanvasTabsProps) {
  const [internalTab, setInternalTab] = useState(tabs[0]?.id ?? "");
  const activeId = activeTabId ?? internalTab;
  const activeTab = tabs.find((tab) => tab.id === activeId) ?? tabs[0];

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeId)) {
      const firstEnabled = tabs.find((tab) => !tab.disabled);
      if (firstEnabled) {
        setInternalTab(firstEnabled.id);
        onTabChange?.(firstEnabled.id);
      }
    }
  }, [tabs, activeId, onTabChange]);

  const selectTab = (id: string) => {
    const tab = tabs.find((t) => t.id === id);
    if (!tab || tab.disabled) return;
    setInternalTab(id);
    onTabChange?.(id);
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      {header}

      <div className="mt-4 flex shrink-0 gap-1 overflow-x-auto border-b border-slate-200 pb-px">
        {tabs.map((tab) => {
          const active = tab.id === activeTab?.id;
          return (
            <button
              key={tab.id}
              type="button"
              disabled={tab.disabled}
              onClick={() => selectTab(tab.id)}
              className={[
                "flex shrink-0 items-center gap-2 rounded-t-lg px-4 py-2.5 text-sm font-medium transition",
                tab.disabled
                  ? "cursor-not-allowed text-slate-300"
                  : active
                    ? "border border-b-0 border-slate-200 bg-white text-indigo-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
              ].join(" ")}
            >
              {tab.label}
              {tab.badge && (
                <span
                  className={[
                    "rounded-full px-2 py-0.5 text-[10px] font-medium",
                    active ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-500",
                  ].join(" ")}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto rounded-b-xl rounded-tr-xl border border-t-0 border-slate-200 bg-white p-4 sm:p-5">
        {activeTab?.content}
      </div>
    </div>
  );
}
