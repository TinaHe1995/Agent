#!/usr/bin/env bash
# Drive OpenHands + DeepSeek to build the project/finance management desktop app.
set -euo pipefail
cd "$(dirname "$0")/.."

# Load gitignored local env files if Cursor Secrets did not inject variables.
if [[ -f .env.local ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.local
  set +a
fi

if [[ -z "${DEEPSEEK_API_KEY:-}${LLM_API_KEY:-}" ]]; then
  echo "Error: DEEPSEEK_API_KEY / LLM_API_KEY not found." >&2
  echo "  1) Cursor Dashboard → Cloud Agents → Environment → Secrets" >&2
  echo "     Name must be exactly: DEEPSEEK_API_KEY" >&2
  echo "  2) Or create repo-root .env.local with: DEEPSEEK_API_KEY=sk-..." >&2
  echo "  3) Save environment and restart Cloud Agent after adding secrets" >&2
  exit 1
fi

echo "==> Building 工程财务管控系统 via OpenHands Agent (DeepSeek)"
echo "    APP_DIR=${APP_DIR:-project-mgmt-desktop/}"
echo ""

exec uv run python scripts/develop_project_mgmt_app.py "$@"
