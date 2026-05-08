"""LLM Profiles router for agent-server.

Provides HTTP endpoints for managing named LLM configurations (profiles).
Profiles are stored as JSON files via LLMProfileStore.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Final

from fastapi import APIRouter, HTTPException, Path, Request, status
from pydantic import BaseModel, Field, SecretStr

from openhands.sdk.llm import LLM
from openhands.sdk.llm.llm_profile_store import LLMProfileStore
from openhands.sdk.logger import get_logger


logger = get_logger(__name__)

profiles_router = APIRouter(prefix="/profiles", tags=["Profiles"])

# Profile name constraints: alphanumerics + . _ - only, 1-64 chars.
# Blocks empty names, path-traversal fragments, and special characters.
_NAME_PATTERN: Final[str] = r"^[A-Za-z0-9._-]{1,64}$"
_NAME_REGEX: Final[re.Pattern[str]] = re.compile(_NAME_PATTERN)

# Maximum number of profiles per user (soft cap)
MAX_PROFILES: Final[int] = 50

ProfileName = Annotated[
    str,
    Path(min_length=1, max_length=64, pattern=_NAME_PATTERN),
]


# ── Response/Request Models ────────────────────────────────────────────────


class ProfileInfo(BaseModel):
    """Profile summary for list endpoint."""

    name: str
    model: str | None = None
    base_url: str | None = None
    api_key_set: bool = False


class ProfileListResponse(BaseModel):
    """Response body for listing profiles."""

    profiles: list[ProfileInfo]


class ProfileDetailResponse(BaseModel):
    """Response body for fetching a single profile.

    ``config.api_key`` is always nulled; use ``api_key_set`` to check if set.
    """

    name: str
    config: dict[str, Any]
    api_key_set: bool = False


class ProfileMutationResponse(BaseModel):
    """Response body for save/delete/rename operations."""

    name: str
    message: str


class SaveProfileRequest(BaseModel):
    """Request body for saving a profile."""

    llm: LLM
    include_secrets: bool = Field(
        default=True,
        description="Whether to persist the API key with the profile.",
    )


class RenameProfileRequest(BaseModel):
    """Request body for renaming a profile."""

    new_name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=_NAME_PATTERN,
    )


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_profile_store(_request: Request) -> LLMProfileStore:
    """Get or create profile store.

    Uses default directory (~/.openhands/profiles).
    The request argument is kept for future extensibility (e.g., per-user stores).
    """
    return LLMProfileStore()


def _has_api_key(llm: LLM) -> bool:
    """Check if LLM has a non-empty API key configured."""
    if llm.api_key is None:
        return False
    secret_value = (
        llm.api_key.get_secret_value()
        if isinstance(llm.api_key, SecretStr)
        else str(llm.api_key)
    )
    return bool(secret_value and secret_value.strip())


def _clean_name(filename: str) -> str:
    """Remove .json extension from filename."""
    return filename.removesuffix(".json")


# ── Endpoints ──────────────────────────────────────────────────────────────


@profiles_router.get("", response_model=ProfileListResponse)
async def list_profiles(request: Request) -> ProfileListResponse:
    """List all saved LLM profiles.

    Returns profile names with basic model info. API keys are never exposed.
    """
    store = _get_profile_store(request)

    try:
        filenames = store.list()
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile store is busy. Please retry.",
        )

    profiles: list[ProfileInfo] = []
    for filename in filenames:
        name = _clean_name(filename)
        try:
            llm = store.load(name)
            profiles.append(
                ProfileInfo(
                    name=name,
                    model=llm.model,
                    base_url=llm.base_url,
                    api_key_set=_has_api_key(llm),
                )
            )
        except (FileNotFoundError, ValueError) as e:
            # Skip corrupted profiles but log warning
            logger.warning(f"Skipping corrupted profile '{name}': {e}")
            continue

    logger.info(f"Listed {len(profiles)} profile(s)")
    return ProfileListResponse(profiles=profiles)


@profiles_router.get("/{name}", response_model=ProfileDetailResponse)
async def get_profile(request: Request, name: ProfileName) -> ProfileDetailResponse:
    """Get a specific profile's configuration.

    Returns the full LLM config with ``api_key`` nulled out.
    """
    store = _get_profile_store(request)

    try:
        llm = store.load(name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{name}' not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile '{name}' is corrupted: {e}",
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile store is busy. Please retry.",
        )

    api_key_set = _has_api_key(llm)
    config = llm.model_dump(mode="json")
    config["api_key"] = None  # Never expose in response

    logger.info(f"Retrieved profile '{name}'")
    return ProfileDetailResponse(name=name, config=config, api_key_set=api_key_set)


@profiles_router.post(
    "/{name}",
    response_model=ProfileMutationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_profile(
    request: Request,
    name: ProfileName,
    body: SaveProfileRequest,
) -> ProfileMutationResponse:
    """Save an LLM configuration as a named profile.

    Overwrites if profile with same name exists. Returns 409 if creating
    a new profile would exceed the profile limit.
    """
    store = _get_profile_store(request)

    # Check profile limit for new profiles
    try:
        existing = store.list()
        clean_existing = [_clean_name(f) for f in existing]
        if name not in clean_existing and len(existing) >= MAX_PROFILES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Profile limit reached ({MAX_PROFILES}). "
                "Delete a profile before saving a new one.",
            )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile store is busy. Please retry.",
        )

    try:
        store.save(name, body.llm, include_secrets=body.include_secrets)
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile store is busy. Please retry.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    logger.info(f"Saved profile '{name}'")
    return ProfileMutationResponse(name=name, message=f"Profile '{name}' saved")


@profiles_router.delete("/{name}", response_model=ProfileMutationResponse)
async def delete_profile(
    request: Request, name: ProfileName
) -> ProfileMutationResponse:
    """Delete a saved profile.

    Idempotent: returns success even if profile didn't exist.
    """
    store = _get_profile_store(request)

    try:
        store.delete(name)
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile store is busy. Please retry.",
        )

    logger.info(f"Deleted profile '{name}'")
    return ProfileMutationResponse(name=name, message=f"Profile '{name}' deleted")


@profiles_router.post("/{name}/rename", response_model=ProfileMutationResponse)
async def rename_profile(
    request: Request,
    name: ProfileName,
    body: RenameProfileRequest,
) -> ProfileMutationResponse:
    """Rename a saved profile.

    Preserves the stored LLM config including api_key.
    Returns 409 if new_name is already in use.
    """
    if name == body.new_name:
        return ProfileMutationResponse(
            name=name,
            message=f"Profile '{name}' unchanged (same name)",
        )

    store = _get_profile_store(request)

    # Check if new name already exists
    try:
        existing = [_clean_name(f) for f in store.list()]
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile store is busy. Please retry.",
        )

    if body.new_name in existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Profile '{body.new_name}' already exists",
        )

    # Load existing profile
    try:
        llm = store.load(name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{name}' not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile '{name}' is corrupted: {e}",
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile store is busy. Please retry.",
        )

    # Save with new name (preserving secrets) then delete old
    try:
        store.save(body.new_name, llm, include_secrets=True)
        store.delete(name)
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile store is busy. Please retry.",
        )

    logger.info(f"Renamed profile '{name}' to '{body.new_name}'")
    return ProfileMutationResponse(
        name=body.new_name,
        message=f"Profile '{name}' renamed to '{body.new_name}'",
    )
