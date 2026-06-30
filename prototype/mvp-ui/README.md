# Agent 工坊 MVP UI 原型

可交互的前端体验原型：**左侧聊天 + 右侧画布 + 三阶段拍板**。

这是一个**纯前端 Demo**，使用模拟 Agent 回复，无需 API 密钥或后端服务。

## 在线体验（推荐）

部署完成后，在浏览器打开：

**https://tinahe1995.github.io/Agent/**

> 若页面 404，请到 GitHub 仓库 **Settings → Pages**，确认 Source 为 **GitHub Actions**。

## 本地运行（在你自己的电脑上）

```bash
cd prototype/mvp-ui
npm install
npm run dev
```

然后打开终端里显示的地址，通常是 **http://localhost:5173**。

### Mock 与真实引擎切换

| 模式 | 配置 | 说明 |
|------|------|------|
| **模拟**（默认） | `VITE_USE_MOCK=true` | 无需后端，适合 GitHub Pages |
| **真实引擎** | `VITE_USE_MOCK=false` | 阶段 3「制作」接入 OpenHands Agent Server |

复制环境变量模板：

```bash
cp .env.example .env.local
```

**真实引擎联调步骤：**

```bash
# 终端 1：仓库根目录
make build
export LLM_API_KEY="你的密钥"
uv run agent-server --port 8000

# 终端 2：MVP UI
cd prototype/mvp-ui
echo "VITE_USE_MOCK=false" > .env.local
npm run dev
```

开发模式下 Vite 会把 `/api`、`/sockets`、`/alive`、`/ready` 代理到 `localhost:8000`。

- 阶段 **0～2**：仍用 `mockAgent`（轻量编排）
- 阶段 **3 制作**：创建 OpenHands 会话，WebSocket 收事件；失败则自动回退模拟
- 左上角徽章显示：**模拟引擎** / **OpenHands 已连接** / **引擎离线**

API 客户端骨架：`src/api/agentServer.ts`

### 为什么在 Cursor 远程环境里打不开 localhost？

如果你是在 **Cursor 云端 / 远程工作区** 里开发：

- `localhost:5173` 指的是**云端机器**，不是你电脑的浏览器
- 需要下面两种方式之一：

**方式 A：Cursor 端口转发（推荐）**

1. 在 Cursor 底部打开 **Ports（端口）** 面板
2. 找到或添加端口 `5173`
3. 点击 **Open in Browser（在浏览器中打开）**

**方式 B：GitHub Pages 在线地址**

使用上面的 **https://tinahe1995.github.io/Agent/** ，无需配置端口。

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
