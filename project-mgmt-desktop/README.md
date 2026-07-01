# 工程财务管控系统

本地运行的工程进度与财务管控小软件，包含：

- **工程进度管控**：项目、任务、加权进度、与计划进度对比
- **财务数据匹配**：预算科目与支出自动匹配、差异分析
- **进度预警**：进度落后或任务逾期时提醒
- **财务预算预警**：支出节奏或总额超预算时提醒
- **月度报表**：按月汇总进度、财务、预警，支持导出 TXT

## 技术栈

- Python 3.12+
- Streamlit（本地浏览器 UI，适合桌面使用）
- SQLite（本地数据持久化）

## 快速启动

```bash
cd project-mgmt-desktop
chmod +x run_app.sh
./run_app.sh
```

或：

```bash
cd project-mgmt-desktop
PYTHONPATH=. uv run streamlit run main.py
```

浏览器打开 http://localhost:8501 即可使用。首次启动会自动创建示例项目数据。

## 使用 OpenHands + DeepSeek 自动开发/扩展

**推荐：使用仓库根目录驱动脚本**

```bash
export DEEPSEEK_API_KEY="你的密钥"
# 或 export LLM_API_KEY="你的密钥"

# 从仓库根目录执行（驱使 Agent 从零构建或完善本应用）
./scripts/develop_project_mgmt_app.sh

# 仅验证已有构建、不调用 Agent
./scripts/develop_project_mgmt_app.sh --verify-only
```

也可在本目录直接调用（等价）：

```bash
uv run python run_with_openhands.py
```

可选环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_MODEL` | `deepseek/deepseek-chat` | DeepSeek 模型 |
| `LLM_BASE_URL` | `https://api.deepseek.com` | API 地址 |
| `PROJECT_WORKSPACE` | 当前目录 | Agent 工作区 |

## 目录结构

```
project-mgmt-desktop/
├── main.py                 # Streamlit 入口
├── run_app.sh              # 一键启动
├── run_with_openhands.py   # OpenHands + DeepSeek 脚本
├── app/
│   ├── database.py         # SQLite
│   ├── services/           # 业务逻辑
│   └── ui/main.py          # 界面
└── data/app.db             # 运行时生成
```

## 功能说明

### 总览
显示加权进度、计划进度、累计支出、预算余额及实时预警。

### 进度管控
管理任务权重与完成度，支持动态更新进度。

### 财务匹配
维护预算科目、登记支出并匹配科目，查看差异表。

### 预警中心
可配置进度落后阈值与预算超支节奏阈值。

### 月度报表
选择年月生成报表，可下载为文本文件。
