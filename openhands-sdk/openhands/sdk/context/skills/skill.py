"""Backward-compatible re-exports. Canonical location: openhands.sdk.skills.skill"""
from openhands.sdk.skills.skill import (  # noqa: F401
    DEFAULT_MARKETPLACE_PATH,
    PUBLIC_SKILLS_REF,
    PUBLIC_SKILLS_REPO,
    Skill,
    load_available_skills,
    load_skills_from_dir,
)

# Backward-compatible alias: PUBLIC_SKILLS_BRANCH was renamed to PUBLIC_SKILLS_REF.
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
