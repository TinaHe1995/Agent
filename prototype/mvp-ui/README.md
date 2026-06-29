# Agent 工坊 MVP UI 原型

可交互的前端体验原型：**左侧聊天 + 右侧画布 + 三阶段拍板**。

这是一个**纯前端 Demo**，使用模拟 Agent 回复，无需 API 密钥或后端服务。

## 快速开始

```bash
cd prototype/mvp-ui
npm install
npm run dev
```

浏览器打开：**http://localhost:5173**

## 体验路径

1. **做什么** — 回答 Agent 问题，右侧实时更新需求摘要，最后确认需求文档
2. **长什么样** — 选择界面风格（A/B），可在聊天中说「按钮大一点」「颜色更暖」
3. **做出来试试** — 观看制作进度，试用预览页面，勾选验收清单后完成

## 技术栈

- React + TypeScript + Vite
- Tailwind CSS v4
- 内置 MVP 状态机（3 阶段、3 个门禁）

## 说明

- 本原型用于验证 UX，不代表真实 Agent 开发能力
- 完整产品需将此前端与 OpenHands SDK 后端对接
