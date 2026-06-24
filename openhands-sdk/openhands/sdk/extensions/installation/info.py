from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    FieldSerializationInfo,
    ValidationInfo,
    field_serializer,
    field_validator,
)

from openhands.sdk.extensions.installation.interface import ExtensionProtocol
from openhands.sdk.utils.pydantic_secrets import (
    serialize_credential_url,
    validate_credential_url,
)


class InstallationInfo(BaseModel):
    """Metadata record for a single installed extension.

    Stored (keyed by name) inside ``InstallationMetadata`` and persisted to
    the ``.installed.json`` file in the installation directory.
    """

    name: str = Field(description="Extension name")
    version: str = Field(default="", description="Extension version")
    description: str = Field(default="", description="Extension description")

    enabled: bool = Field(default=True, description="Whether the extension is enabled")

    source: str = Field(description="Original source (e.g., 'github:owner/repo')")
    resolved_ref: str | None = Field(
        default=None, description="Resolved git commit SHA (for version pinning)"
    )
    repo_path: str | None = Field(
        default=None,
        description="Subdirectory path within the repository (for monorepos)",
    )

    installed_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 timestamp of installation",
    )
    install_path: Path = Field(description="Path where the extension is installed")

    @field_validator("source", mode="before")
    @classmethod
    def _decrypt_source(cls, v: Any, info: ValidationInfo) -> Any:
        """Decrypt at-rest ciphertext (see validate_credential_url)."""
        return validate_credential_url(v, info)

    @field_serializer("source", when_used="always")
    def _serialize_source(self, source: str, info: FieldSerializationInfo) -> str:
        """Redact/expose/encrypt by context (see serialize_credential_url)."""
        return serialize_credential_url(source, info)

    @staticmethod
    def from_extension(
        extension: ExtensionProtocol,
        source: str,
        install_path: Path,
        resolved_ref: str | None = None,
        repo_path: str | None = None,
    ) -> InstallationInfo:
        """Create an InstallationInfo from an extension and its install context.

        Args:
            extension: Any object satisfying ``ExtensionProtocol``.
            source: Original source string (e.g. ``"github:owner/repo"``).
            install_path: Filesystem path the extension was copied to.
            resolved_ref: Resolved git commit SHA, if applicable.
            repo_path: Subdirectory within a monorepo, if applicable.
        """
        return InstallationInfo(
            name=extension.name,
            version=extension.version,
            description=extension.description or "",
            source=source,
            resolved_ref=resolved_ref,
            repo_path=repo_path,
            install_path=install_path,
        )
