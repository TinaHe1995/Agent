"""
Use OpenHands Agent + DeepSeek API to develop or extend the desktop app.

Environment variables (any one API key style works):
  DEEPSEEK_API_KEY  — preferred for DeepSeek
  LLM_API_KEY       — fallback

Optional:
  LLM_MODEL         — default: deepseek/deepseek-chat
  LLM_BASE_URL      — default: https://api.deepseek.com
  PROJECT_WORKSPACE — where the agent writes files (default: this directory)
"""

import os
import sys
from pathlib import Path

from pydantic import SecretStr

from openhands.sdk import LLM, Conversation, get_logger
from openhands.tools.preset.default import get_default_agent


logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parent

TASK_PROMPT = """
请在当前工作区完善「工程财务管控系统」桌面应用（Python + Streamlit），要求：

1. 工程进度管控：项目、任务、加权进度、计划进度对比
2. 财务数据匹配：预算科目与支出匹配、差异分析
3. 进度预警：实际进度落后计划进度时告警
4. 财务预算预警：支出节奏或总额超预算时告警
5. 月度报表：按月份汇总进度、财务、预警，支持导出

若应用已存在（project-mgmt-desktop/），请检查功能完整性、修复问题、补充测试与 README。
完成后运行验证命令并写一份 IMPLEMENTATION_SUMMARY.md。
""".strip()


def resolve_api_key() -> str:
    for name in ("DEEPSEEK_API_KEY", "LLM_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(name)
        if value:
            return value
    logger.error(
        "未找到 API Key。请设置 DEEPSEEK_API_KEY 或 LLM_API_KEY 环境变量。"
    )
    sys.exit(1)


def main() -> None:
    api_key = resolve_api_key()
    model = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    workspace = os.getenv("PROJECT_WORKSPACE", str(ROOT))

    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
        usage_id="project_mgmt_build",
        drop_params=True,
    )

    agent = get_default_agent(llm=llm, cli_mode=True)
    conversation = Conversation(agent=agent, workspace=workspace)

    logger.info("Workspace: %s", workspace)
    logger.info("Model: %s", model)
    logger.info("Starting agent task...")

    conversation.send_message(TASK_PROMPT)
    conversation.run()

    status = conversation.state.execution_status
    logger.info("Agent run finished with status: %s", status)
    print("EXAMPLE_COST: 0")


if __name__ == "__main__":
    main()
