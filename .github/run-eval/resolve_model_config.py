"""Compatibility shim for model resolution now owned by OpenHands/evaluation.

The model registry was moved to OpenHands/evaluation. This file exists only so
base-branch `pull_request_target` workflows that still import this path can run
against PR branches while the workflow migration is in flight.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

_REPO = "https://github.com/OpenHands/evaluation.git"
_RELATIVE_RESOLVER = Path("eval-job/model-config/resolve_model_config.py")
_FALLBACK_REF = "feat/port-model-resolution"


def _candidate_refs() -> list[str]:
    refs = [os.environ.get("EVALUATION_MODEL_CONFIG_REF", "main"), _FALLBACK_REF]
    seen = set()
    return [ref for ref in refs if ref and not (ref in seen or seen.add(ref))]


def _checkout_resolver(ref: str, target: Path) -> Path:
    if target.exists():
        shutil.rmtree(target)
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--sparse",
            "--branch",
            ref,
            _REPO,
            str(target),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "-C", str(target), "sparse-checkout", "set", "eval-job/model-config"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    resolver = target / _RELATIVE_RESOLVER
    if not resolver.exists():
        raise FileNotFoundError(resolver)
    return resolver


def _load_evaluation_resolver() -> ModuleType:
    base = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir()))
    last_error: Exception | None = None
    for ref in _candidate_refs():
        try:
            resolver = _checkout_resolver(ref, base / "evaluation-model-config")
            spec = importlib.util.spec_from_file_location(
                "_evaluation_resolve_model_config", resolver
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load resolver from {resolver}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
        except Exception as exc:  # pragma: no cover - exercised in GitHub Actions
            last_error = exc
    raise RuntimeError("Failed to load model resolver from OpenHands/evaluation") from last_error


_resolver = _load_evaluation_resolver()


def __getattr__(name: str) -> Any:
    return getattr(_resolver, name)
