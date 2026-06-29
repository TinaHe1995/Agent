import type { RequirementsData, StyleOption } from "./types";

export interface QuestionStep {
  id: string;
  prompt: string;
  quickReplies?: string[];
  applyAnswer: (answer: string, current: RequirementsData) => Partial<RequirementsData>;
}

export const TECH_OPTIONS = [
  {
    id: "web" as const,
    name: "网页应用",
    summary: "手机电脑都能用，后续扩展性好",
    cost: "维护成本：中",
    recommended: true,
  },
  {
    id: "wechat" as const,
    name: "微信小程序",
    summary: "员工在微信里打开，上手快",
    cost: "维护成本：中",
  },
  {
    id: "desktop" as const,
    name: "本地小工具",
    summary: "仅行政电脑使用，上线最快",
    cost: "维护成本：低",
  },
];

export const DISCOVERY_FLOW = [
  {
    prompt:
      "你好，我是你的项目助手。\n\n先不用急着做软件——我想先帮你判断：这个问题是否值得自己做。\n\n你想解决什么问题？",
    quickReplies: ["员工请假登记麻烦", "活动报名收集", "想做一个内部小工具"],
    applyAnswer: (answer: string) => answer,
  },
  {
    prompt: "大概多少人用？对费用和时间敏感吗？",
    quickReplies: ["20人小公司，预算有限", "50人左右，希望尽快", "不急，想先搞清楚"],
    applyAnswer: (answer: string) => answer,
  },
];

export const QUESTION_FLOW: QuestionStep[] = [
  {
    id: "goal",
    prompt:
      "我们按自研来做。先把需求说清楚。\n\n你想做一个什么东西？最想解决的一个问题是什么？",
    quickReplies: ["员工请假登记", "活动报名收集", "简易待办清单"],
    applyAnswer: (answer) => ({
      goal: answer.includes("请假")
        ? "让员工在线登记请假，行政一键导出 Excel"
        : answer.includes("报名")
          ? "做一个活动报名页，收集参与者信息"
          : answer.includes("待办")
            ? "做一个简单的个人待办清单"
            : answer,
    }),
  },
  {
    id: "users",
    prompt: "谁会使用这个工具？大概多少人？",
    quickReplies: ["20人小公司，员工+行政", "部门内部约50人", "仅自己使用"],
    applyAnswer: (answer) => ({
      users: answer,
    }),
  },
  {
    id: "p0",
    prompt: "最重要的 3 个功能是什么？你可以直接说，我会帮你整理。",
    quickReplies: [
      "登记请假、导出Excel、手机可用",
      "报名表单、人数统计、导出名单",
      "新增待办、标记完成、按日期筛选",
    ],
    applyAnswer: (answer) => {
      if (answer.includes("请假")) {
        return {
          p0Features: ["在线请假登记", "导出 Excel", "手机浏览器可用"],
          p1Features: ["按月份筛选"],
        };
      }
      if (answer.includes("报名")) {
        return {
          p0Features: ["在线报名表单", "人数统计", "导出名单"],
          p1Features: ["报名截止时间提醒"],
        };
      }
      return {
        p0Features: answer.split(/[、,，]/).map((s) => s.trim()).filter(Boolean).slice(0, 3),
        p1Features: ["按日期筛选"],
      };
    },
  },
  {
    id: "acceptance",
    prompt: "怎样算“做完了”？请举 1～2 个你能直接判断的例子。",
    quickReplies: [
      "员工1分钟能登记，行政10秒能导出",
      "报名者3步完成报名",
      "新增一条待办不超过30秒",
    ],
    applyAnswer: (answer) => ({
      acceptance: answer.includes("登记")
        ? [
            "员工 1 分钟内完成登记",
            "行政 10 秒内导出当月数据",
            "手机浏览器可正常使用",
          ]
        : answer.split(/[，,]/).map((s) => s.trim()).filter(Boolean).slice(0, 3),
    }),
  },
  {
    id: "scope",
    prompt: "有什么是你明确不想要的？这能帮我们避免做错方向。",
    quickReplies: ["不做审批流", "不做支付功能", "不连接现有HR系统"],
    applyAnswer: (answer) => ({
      outOfScope: answer.split(/[、,，]/).map((s) => s.trim()).filter(Boolean),
    }),
  },
  {
    id: "timeline",
    prompt: "你希望多久能看到第一版可以试用的东西？",
    quickReplies: ["2周内", "1个月内", "不急，先做出来看看"],
    applyAnswer: (answer) => ({
      timeline: answer,
    }),
  },
];

export const STYLE_OPTIONS: StyleOption[] = [
  {
    id: "A",
    name: "简洁办公",
    description: "蓝灰白配色，干净利落，适合日常办公场景",
    colors: ["#2563eb", "#f8fafc", "#0f172a"],
  },
  {
    id: "B",
    name: "温暖亲和",
    description: "米白与暖橙，按钮更醒目，适合非技术同事使用",
    colors: ["#ea580c", "#fff7ed", "#431407"],
    recommended: true,
  },
];

export function detectStyleFeedback(text: string): {
  warmth?: number;
  buttonSize?: number;
  reply: string;
} | null {
  let warmth: number | undefined;
  let buttonSize: number | undefined;
  const parts: string[] = [];

  if (/暖|温暖|橙|鲜艳/.test(text)) {
    warmth = 80;
    parts.push("已把整体色调调暖");
  }
  if (/冷|蓝|素/.test(text)) {
    warmth = 25;
    parts.push("已调整为更冷静的配色");
  }
  if (/按钮.*大|大一点|更大/.test(text)) {
    buttonSize = 85;
    parts.push("已加大主按钮尺寸");
  }
  if (/按钮.*小|简约/.test(text)) {
    buttonSize = 35;
    parts.push("已缩小按钮，让页面更简约");
  }

  if (parts.length === 0) return null;

  return {
    warmth,
    buttonSize,
    reply: `好的，${parts.join("，")}。请查看右侧更新后的风格预览（v${Date.now() % 9 + 2}）。满意的话请点击「确认风格，开始制作」。`,
  };
}

export function detectBuildFeedback(text: string): string | null {
  if (/手机|移动端|打不开/.test(text)) {
    return "收到，我会优先修复手机端显示问题，并调整导出字段顺序。请稍等，正在更新预览…";
  }
  if (/导出|excel|字段|顺序/.test(text)) {
    return "好的，我会把导出字段顺序调整为：姓名、部门、日期、事由。正在更新预览…";
  }
  if (/颜色|样式|按钮/.test(text)) {
    return "这是功能问题还是样式问题？如果是样式，我们可以回到风格阶段微调；如果是功能，我会直接修复。";
  }
  return null;
}
