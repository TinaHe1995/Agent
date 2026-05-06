"""API request and response models for settings endpoints.

These models define the contract between SDK clients and agent-server settings
endpoints. They are defined in the SDK so both packages can share them without
circular dependencies (SDK cannot import from agent-server, but agent-server
can import from SDK).

Server-side usage:
    The agent-server imports these models and uses them as FastAPI response_model.

Client-side usage:
    RemoteWorkspace uses these models to validate responses from settings APIs.
"""

from typing import Any

from pydantic import BaseModel, SecretStr


# ── Settings API Models ───────────────────────────────────────────────────


class SettingsResponse(BaseModel):
    """Response model for GET /api/settings.

    Contains the full settings payload including agent configuration,
    conversation settings, and a flag indicating if an LLM API key is set.
    """

    agent_settings: dict[str, Any]
    conversation_settings: dict[str, Any]
    llm_api_key_is_set: bool


class SettingsUpdateRequest(BaseModel):
    """Request model for PATCH /api/settings.

    Supports partial updates via diff objects that are deep-merged with
    existing settings.
    """

    agent_settings_diff: dict[str, Any] | None = None
    conversation_settings_diff: dict[str, Any] | None = None


# ── Secrets API Models ────────────────────────────────────────────────────


class SecretItemResponse(BaseModel):
    """Response model for a secret item (without value).

    Used in list responses and as the response for create/update operations.
    """

    name: str
    description: str | None = None


class SecretsListResponse(BaseModel):
    """Response model for GET /api/settings/secrets.

    Lists all available secrets with their names and descriptions.
    Values are never included in list responses.
    """

    secrets: list[SecretItemResponse]


class SecretCreateRequest(BaseModel):
    """Request model for PUT /api/settings/secrets.

    Creates or updates a secret with the given name and value.
    """

    name: str
    value: SecretStr
    description: str | None = None
