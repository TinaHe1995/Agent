"""API request and response models for settings endpoints.

These models define the contract between SDK clients and agent-server settings
endpoints. They are defined in the SDK so both packages can share them without
circular dependencies (SDK cannot import from agent-server, but agent-server
can import from SDK).

Server-side usage:
    The agent-server imports these models and uses them as FastAPI response_model.

Client-side usage:
    RemoteWorkspace uses these models to validate responses from settings APIs.
    Use the typed accessor methods (``get_agent_settings()``,
    ``get_conversation_settings()``) to parse the raw dicts into typed models.

Note on dict fields:
    ``SettingsResponse`` uses ``dict[str, Any]`` for ``agent_settings`` and
    ``conversation_settings`` rather than typed models because the server needs
    to control how secrets are serialized (plaintext/encrypted/redacted) via
    serialization context. Typed Pydantic fields would lose this context during
    FastAPI's automatic JSON serialization.

    Clients that need type safety should use the accessor methods which validate
    the dicts into ``AgentSettingsConfig`` and ``ConversationSettings``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr


if TYPE_CHECKING:
    from .model import AgentSettingsConfig, ConversationSettings


# ── Misc Settings (frontend-owned, not interpreted by the agent) ─────────


class AppPreferences(BaseModel):
    """Frontend app-level user preferences that don't affect agent execution.

    These fields are app/UI-level metadata (preferred language, sound
    notifications, analytics opt-in, git identity used for in-conversation
    commits) plus the list of skills the user has disabled. The agent-server
    persists them alongside agent/conversation settings but does not interpret
    them — the cloud equivalent (``POST /api/v1/settings``) accepts the same
    keys at the top level, so frontends can use a single shape for both
    backends.

    Field semantics:

    - ``language``, ``git_user_name``, ``git_user_email``: ``None`` means "no
      preference set" (the frontend can fall back to its own default).
    - ``user_consents_to_analytics``: tri-state — ``None`` means "not yet
      asked", ``True``/``False`` are explicit answers.
    - ``enable_sound_notifications``: ``None`` means "use frontend default";
      ``True``/``False`` are explicit user choices.
    - ``disabled_skills``: list of skill identifiers the user has disabled.
      Defaults to an empty list (no skills disabled).

    .. note::

       Persisted as ``misc_settings.app_preferences`` since persisted-settings
       schema v2. The wrapper :class:`MiscSettings` is the addressable block
       on :class:`SettingsResponse`; this class is only the inner payload.
    """

    language: str | None = None
    user_consents_to_analytics: bool | None = None
    enable_sound_notifications: bool | None = None
    git_user_name: str | None = None
    git_user_email: str | None = None
    disabled_skills: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class MiscSettings(BaseModel):
    """Container for frontend-owned settings that the agent doesn't interpret.

    A single addressable block on :class:`SettingsResponse` so the API has one
    extension point for "settings the frontend wants persisted, but the agent
    doesn't act on". Currently holds :class:`AppPreferences`; new categories
    (e.g. UI preferences, layout state) can be added as additional nested
    fields without churning the top-level API shape.

    Persisted as ``misc_settings`` on :class:`PersistedSettings` (schema v2+).
    Updated through ``misc_settings_diff`` on :class:`SettingsUpdateRequest`,
    which is deep-merged into the existing block — so a partial diff like
    ``{"app_preferences": {"language": "fr"}}`` updates only ``language`` and
    leaves every other ``app_preferences`` field alone.
    """

    app_preferences: AppPreferences = Field(default_factory=AppPreferences)

    model_config = ConfigDict(extra="ignore")


# ── Settings API Models ───────────────────────────────────────────────────


class SettingsResponse(BaseModel):
    """Response model for GET /api/settings.

    Contains the full settings payload including agent configuration,
    conversation settings, miscellaneous frontend-owned settings, and a flag
    indicating whether an LLM API key is set.

    The ``agent_settings`` and ``conversation_settings`` fields are raw dicts
    because the server controls secret serialization via context. Use the
    typed accessor methods for validation:

    Example::

        response = SettingsResponse.model_validate(api_response.json())
        agent = response.get_agent_settings()  # Returns AgentSettingsConfig
        conv = response.get_conversation_settings()  # Returns ConversationSettings
        prefs = response.misc_settings.app_preferences  # Already typed
    """

    agent_settings: dict[str, Any]
    conversation_settings: dict[str, Any]
    llm_api_key_is_set: bool
    misc_settings: MiscSettings = Field(default_factory=MiscSettings)

    def get_agent_settings(self) -> AgentSettingsConfig:
        """Parse and validate ``agent_settings`` into a typed model.

        Returns:
            The validated agent settings as either ``OpenHandsAgentSettings``
            or ``ACPAgentSettings`` depending on the ``agent_kind`` discriminator.
        """
        from .model import validate_agent_settings

        return validate_agent_settings(self.agent_settings)

    def get_conversation_settings(self) -> ConversationSettings:
        """Parse and validate ``conversation_settings`` into a typed model.

        Returns:
            The validated conversation settings.
        """
        from .model import ConversationSettings

        return ConversationSettings.from_persisted(self.conversation_settings)


class SettingsUpdateRequest(BaseModel):
    """Request model for PATCH /api/settings.

    Supports partial updates via diff objects that are deep-merged with
    existing settings.

    ``misc_settings_diff`` accepts a partial :class:`MiscSettings` dict and is
    deep-merged into the persisted block, matching the semantics of
    ``agent_settings_diff`` and ``conversation_settings_diff``. So a partial
    payload like ``{"misc_settings_diff": {"app_preferences": {"language":
    "fr"}}}`` updates only the ``language`` field of ``app_preferences``;
    every other field is left alone. Lists (e.g. ``disabled_skills``) are
    replaced wholesale rather than merged.
    """

    agent_settings_diff: dict[str, Any] | None = None
    conversation_settings_diff: dict[str, Any] | None = None
    misc_settings_diff: dict[str, Any] | None = None


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
