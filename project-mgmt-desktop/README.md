# Agent 工作区：工程财务管控系统

本目录是 **OpenHands Agent 的开发输出目录**，不是预置成品。

请使用仓库根目录的驱动脚本，让 Agent 在本目录内从零开发应用：

```bash
# 在仓库根目录执行
export DEEPSEEK_API_KEY="你的密钥"

./scripts/develop_project_mgmt_app.sh
```

Agent 将在此目录创建代码、测试和启动脚本。开发完成后：

```bash
cd project-mgmt-desktop
./run_app.sh    # 由 Agent 生成
```

## 任务要求

开发可在电脑上使用的小软件，包含：

1. 工程进度管控
2. 财务数据匹配
3. 进度预警
4. 财务预算预警
5. 月度报表

详细任务说明见 `scripts/develop_project_mgmt_app.py` 中的 `TASK_PROMPT`。
