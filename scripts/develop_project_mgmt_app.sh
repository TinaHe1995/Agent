#!/usr/bin/env bash
# Drive OpenHands + DeepSeek to build the project/finance management desktop app.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -z "${DEEPSEEK_API_KEY:-}${LLM_API_KEY:-}" ]]; then
  echo "Error: set DEEPSEEK_API_KEY or LLM_API_KEY before running." >&2
  exit 1
fi

echo "==> Building 工程财务管控系统 via OpenHands Agent (DeepSeek)"
echo "    APP_DIR=${APP_DIR:-project-mgmt-desktop/}"
echo ""

exec uv run python scripts/develop_project_mgmt_app.py "$@"
