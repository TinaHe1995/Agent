"""Storage for *meta-profiles*: declarative model-routing configurations.

A meta-profile describes how to pick an LLM for a task. It names a
``classifier_model`` used to categorize the task, a ``default_model`` to fall
back to, and a list of ``classes`` mapping a natural-language task description
to the model that should handle it.

Every model reference (``classifier_model``, ``default_model`` and each
class's ``model``) is the *name of a saved LLM profile* in
:class:`~openhands.sdk.llm.llm_profile_store.LLMProfileStore`, so credentials
and provider settings are resolved through the existing profile machinery.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from pydantic import BaseModel, Field

from openhands.sdk.llm.llm_profile_store import PROFILE_NAME_REGEX
from openhands.sdk.logger import get_logger


_DEFAULT_META_PROFILE_DIR: Final[Path] = Path.home() / ".openhands" / "meta-profiles"

logger = get_logger(__name__)


class MetaProfileClass(BaseModel):
    """A single task category and the LLM profile that should handle it."""

    description: str = Field(
        description="Natural-language description of the kind of task this "
        "class covers (e.g. 'task is UI oriented or requires looking at images')."
    )
    model: str = Field(
        description="Name of the saved LLM profile to switch to for tasks "
        "matching this class."
    )


class MetaProfile(BaseModel):
    """A declarative model-routing configuration."""

    classifier_model: str = Field(
        description="Name of the saved LLM profile used to classify the task."
    )
    default_model: str = Field(
        description="Name of the saved LLM profile to use when no class matches."
    )
    classes: list[MetaProfileClass] = Field(
        default_factory=list,
        description="Ordered list of task classes and their target profiles.",
    )


class MetaProfileStore:
    """Read meta-profiles from ``~/.openhands/meta-profiles`` (by default)."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        """Initialize the meta-profile store.

        Args:
            base_dir: Directory where meta-profiles are stored. Defaults to
                ``~/.openhands/meta-profiles`` when ``None``.
        """
        self.base_dir = (
            Path(base_dir) if base_dir is not None else _DEFAULT_META_PROFILE_DIR
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[str]:
        """Return the names (without ``.json``) of all stored meta-profiles."""
        return sorted(
            p.stem
            for p in self.base_dir.glob("*.json")
            if PROFILE_NAME_REGEX.match(p.stem)
        )

    def _get_path(self, name: str) -> Path:
        clean_name = name.removesuffix(".json")
        if not PROFILE_NAME_REGEX.match(clean_name):
            raise ValueError(
                f"Invalid meta-profile name: {name!r}. "
                "Names must be 1-64 characters, start with a letter or digit, "
                "and contain only letters, digits, '.', '_', or '-'."
            )
        return self.base_dir / f"{clean_name}.json"

    def load(self, name: str) -> MetaProfile:
        """Load a meta-profile by name.

        Raises:
            FileNotFoundError: If the meta-profile does not exist.
            ValueError: If the file is corrupted or fails validation.
        """
        path = self._get_path(name)
        if not path.exists():
            existing = self.list()
            raise FileNotFoundError(
                f"Meta-profile `{name}` not found. "
                f"Available meta-profiles: {', '.join(existing) or 'none'}"
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return MetaProfile.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to load meta-profile `{name}`: {e}") from e
