"""Backward-compatible re-exports from openhands.sdk.skills.

The canonical location is ``openhands.sdk.skills``. These aliases are
kept so that the installed ``openhands.agent_server`` package (which
may be pinned to an older release) can still import from the old path.
"""
from openhands.sdk.skills.skill import (  # noqa: F401
    DEFAULT_MARKETPLACE_PATH,
    PUBLIC_SKILLS_REF,
    PUBLIC_SKILLS_REPO,
    Skill,
    load_available_skills,
    load_skills_from_dir,
)

# Backward-compatible alias: PUBLIC_SKILLS_BRANCH was renamed to
# PUBLIC_SKILLS_REF in the main merge; keep the old name so that
# older installed openhands.agent_server builds can still import it.
PUBLIC_SKILLS_BRANCH = PUBLIC_SKILLS_REF

__all__ = [
    "DEFAULT_MARKETPLACE_PATH",
    "PUBLIC_SKILLS_BRANCH",
    "PUBLIC_SKILLS_REF",
    "PUBLIC_SKILLS_REPO",
    "Skill",
    "load_available_skills",
    "load_skills_from_dir",
]
