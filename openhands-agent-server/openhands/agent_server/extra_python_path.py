"""Helper for prepending external directories to ``sys.path``.

Used so PyInstaller frozen binaries can import external custom-tool ``.py``
files via ``importlib.PathFinder`` (which stays active alongside
``FrozenImporter``). The directories come from the ``--extra-python-path`` CLI
flag or the ``OH_EXTRA_PYTHON_PATH`` environment variable.
"""

import os
import sys

from openhands.sdk.logger import get_logger


logger = get_logger(__name__)

OH_EXTRA_PYTHON_PATH_ENV = "OH_EXTRA_PYTHON_PATH"


def apply_extra_python_path(extra_paths_arg: str | None) -> None:
    """Prepend OS-pathsep-separated paths to ``sys.path``.

    No-ops when ``extra_paths_arg`` is None/empty. Skips paths already on
    ``sys.path`` so repeated calls are idempotent.
    """
    if not extra_paths_arg:
        return
    for raw in extra_paths_arg.split(os.pathsep):
        path = raw.strip()
        if not path:
            continue
        if path not in sys.path:
            sys.path.insert(0, path)
            logger.info("Added to sys.path (extra_python_path): %s", path)


def apply_extra_python_path_from_env() -> None:
    """Apply ``OH_EXTRA_PYTHON_PATH`` from the environment, if set."""
    apply_extra_python_path(os.environ.get(OH_EXTRA_PYTHON_PATH_ENV))
