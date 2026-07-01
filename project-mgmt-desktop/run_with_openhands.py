"""Delegate to scripts/develop_project_mgmt_app.py.

See project-mgmt-desktop/README.md for usage.
"""

import runpy
import sys
from pathlib import Path


_REPO_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "develop_project_mgmt_app.py"
)
sys.argv[0] = str(_REPO_SCRIPT)
runpy.run_path(str(_REPO_SCRIPT), run_name="__main__")
