#!/usr/bin/env python3
"""
Drive OpenHands Agent to build the project/finance management desktop app.

Uses DeepSeek API (or any LiteLLM-compatible provider) and the SDK default
tools (terminal, file_editor, task_tracker) to implement:

  - 工程进度管控
  - 财务数据匹配
  - 进度预警
  - 财务预算预警
  - 月度报表

Usage:
    export DEEPSEEK_API_KEY="sk-..."
    uv run python scripts/develop_project_mgmt_app.py

    # Optional: verify only (no agent run)
    uv run python scripts/develop_project_mgmt_app.py --verify-only

Environment:
    DEEPSEEK_API_KEY   Preferred API key for DeepSeek
    LLM_API_KEY        Fallback API key
    LLM_MODEL          Default: deepseek/deepseek-chat
    LLM_BASE_URL       Default: https://api.deepseek.com
    APP_DIR            Output directory (default: project-mgmt-desktop/)
    SKIP_VERIFY        Set to 1 to skip post-run checks
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from pydantic import SecretStr

from openhands.sdk import LLM, Conversation, get_logger
from openhands.sdk.conversation.state import ConversationExecutionStatus
from openhands.tools.preset.default import get_default_agent


logger = get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_APP_DIR = REPO_ROOT / "project-mgmt-desktop"

TASK_PROMPT = """
请在本工作区开发一个可在电脑上使用的「工程财务管控系统」小软件。

## 目标功能（必须全部实现）

1. **工程进度管控**
   - 支持多个工程项目
   - 每个项目有任务列表、任务权重、完成百分比
   - 计算加权总进度，并与按时间线推算的「计划进度」对比

2. **财务数据匹配**
   - 每个项目有预算科目（如设计费、材料费、人工费）
   - 可登记支出并匹配到预算科目
   - 展示预算 vs 实际 vs 差异

3. **进度预警**
   - 当实际进度落后计划进度超过阈值时告警
   - 任务逾期未完成时告警

4. **财务预算预警**
   - 当支出占预算比例高于计划消耗节奏超过阈值时告警
   - 总支出超过项目总预算时告警

5. **月度报表**
   - 按选择的年月生成报表（进度、财务、匹配、预警）
   - 支持导出为文本文件

## 技术要求

- 语言：Python 3.12+
- UI：优先 Streamlit（本地浏览器访问，适合桌面使用）；若环境支持也可用 tkinter/PyQt
- 数据：SQLite 本地持久化，放在 `data/` 目录
- 代码结构清晰：`app/services/` 分模块，`main.py` 为入口
- 提供 `run_app.sh` 一键启动脚本
- 首次启动可加载演示数据方便体验
- 编写 `README.md` 说明功能与启动方式
- 编写 `tests/test_services.py` 覆盖核心业务逻辑

## 工作区约定

- 所有代码写入当前工作区根目录（即 APP_DIR）
- 不要修改工作区以外的 monorepo 文件

## 完成标准

1. 实现上述全部功能并可本地启动
2. 运行 `PYTHONPATH=. uv run pytest tests/ -q` 通过
3. 在 `IMPLEMENTATION_SUMMARY.md` 中写明：功能清单、启动命令、目录结构
""".strip()


def _load_dotenv_files() -> None:
    """Load KEY=VALUE pairs from gitignored .env.local files if present."""
    paths = (
        REPO_ROOT / ".env.local",
        REPO_ROOT / ".env",
        DEFAULT_APP_DIR / ".env.local",
    )
    for path in paths:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        logger.info("Loaded environment from %s", path)


def resolve_api_key() -> str:
    _load_dotenv_files()
    for name in ("DEEPSEEK_API_KEY", "LLM_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(name)
        if value:
            logger.info("Using API key from %s", name)
            return value
    logger.error(
        "未找到 API Key。请在 Cursor Cloud Secrets 中设置 DEEPSEEK_API_KEY，"
        "或在仓库根目录创建 .env.local（已 gitignore），然后重新启动 Agent。"
    )
    logger.error(
        "诊断：当前进程中 DEEPSEEK_API_KEY=%s, LLM_API_KEY=%s",
        "set" if os.getenv("DEEPSEEK_API_KEY") else "missing",
        "set" if os.getenv("LLM_API_KEY") else "missing",
    )
    sys.exit(1)


def ensure_app_dir(app_dir: Path) -> None:
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "data").mkdir(exist_ok=True)


def run_agent(app_dir: Path) -> ConversationExecutionStatus:
    api_key = resolve_api_key()
    model = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")

    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
        usage_id="develop_project_mgmt_app",
        drop_params=True,
    )

    agent = get_default_agent(llm=llm, cli_mode=True)
    conversation = Conversation(agent=agent, workspace=str(app_dir))

    logger.info("Workspace: %s", app_dir)
    logger.info("Model: %s @ %s", model, base_url)
    logger.info("Dispatching agent task...")

    conversation.send_message(TASK_PROMPT)
    conversation.run()

    status = conversation.state.execution_status
    logger.info("Agent finished with status: %s", status)
    return status


def verify_app(app_dir: Path) -> bool:
    """Run post-build checks without starting Streamlit."""
    main_py = app_dir / "main.py"
    if not main_py.is_file():
        logger.warning(
            "No main.py in %s — agent may not have finished. Skip or re-run.",
            app_dir,
        )
        return False

    checks: list[tuple[str, bool]] = []

    required = [
        app_dir / "main.py",
        app_dir / "README.md",
        app_dir / "run_app.sh",
    ]
    for path in required:
        checks.append((f"exists {path.name}", path.is_file()))

    test_dir = app_dir / "tests"
    if test_dir.is_dir():
        result = subprocess.run(
            ["uv", "run", "pytest", "tests/", "-q"],
            cwd=app_dir,
            env={**os.environ, "PYTHONPATH": str(app_dir)},
            capture_output=True,
            text=True,
        )
        ok = result.returncode == 0
        checks.append(("pytest tests/", ok))
        if not ok:
            logger.error("pytest output:\n%s", result.stdout + result.stderr)
    else:
        checks.append(("tests/ directory", False))

    import_result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-c",
            "from app.ui.main import run_app; print('import ok')",
        ],
        cwd=app_dir,
        env={**os.environ, "PYTHONPATH": str(app_dir)},
        capture_output=True,
        text=True,
    )
    checks.append(("import app.ui.main", import_result.returncode == 0))

    all_ok = True
    for name, ok in checks:
        mark = "OK" if ok else "FAIL"
        logger.info("  [%s] %s", mark, name)
        all_ok = all_ok and ok

    return all_ok


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use OpenHands Agent + DeepSeek to build the project-mgmt app"
    )
    parser.add_argument(
        "--app-dir",
        type=Path,
        default=Path(os.getenv("APP_DIR", str(DEFAULT_APP_DIR))),
        help="Directory where the app will be built (default: project-mgmt-desktop/)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip agent run; only verify an existing build",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip post-run verification",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app_dir = args.app_dir.resolve()
    ensure_app_dir(app_dir)

    if not args.verify_only:
        status = run_agent(app_dir)
        if status == ConversationExecutionStatus.ERROR:
            logger.error("Agent run ended with ERROR")
            sys.exit(1)

    if args.skip_verify or os.getenv("SKIP_VERIFY") == "1":
        print("EXAMPLE_COST: 0")
        return

    logger.info("Running post-build verification...")
    if not verify_app(app_dir):
        logger.error("Verification failed. Check logs above.")
        sys.exit(1)

    logger.info("All checks passed. Launch with: cd %s && ./run_app.sh", app_dir)
    print("EXAMPLE_COST: 0")


if __name__ == "__main__":
    main()
