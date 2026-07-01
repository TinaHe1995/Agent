#!/usr/bin/env bash
# Launch the project management desktop app in your browser.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
echo "Starting 工程财务管控系统 at http://localhost:8501"
exec uv run streamlit run main.py --server.headless true --browser.gatherUsageStats false
