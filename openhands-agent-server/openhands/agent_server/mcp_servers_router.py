"""CRUD endpoints for MCP servers persisted inside agent settings.

Why a dedicated router (rather than going through ``PATCH /api/settings``)

Today, MCP servers live as a dict under
``agent_settings.mcp_config.mcpServers``. Editing a single server through
the global settings PATCH means:

* Read-modify-write of the *whole* collection (because ``mcp_config`` is a
  single Pydantic field that replaces wholesale on assignment-style PATCH;
  even with deep-merge, ``mcpServers`` is a dict where any individual
  key-replace via PATCH affects only that key but still forces the client
  to ship the entire ``mcpServers`` it wants to keep when *adding* or
  *removing* anything else atomically). In practice clients fetch the
  whole encrypted config, splice in their edit, and write the whole thing
  back — which round-trips every *other* server's ``env``/``headers``
  ciphertexts through the client unnecessarily.

* No per-server concurrency. Two clients each adding a *different* server
  race; even with optimistic concurrency at the global-settings level,
  one of them has to retry, having done no work that conflicts with the
  other.

* No discoverable shape — ``mcp_config`` is documented in OpenAPI as one
  big blob; adding a server is undocumented in the API surface.

This router exposes the per-server resource directly:

* ``GET    /api/settings/mcp-servers``         list summaries (no secrets)
* ``GET    /api/settings/mcp-servers/{name}``  read one (X-Expose-Secrets aware)
* ``PUT    /api/settings/mcp-servers/{name}``  upsert one
* ``PATCH  /api/settings/mcp-servers/{name}``  partial edit of one
* ``DELETE /api/settings/mcp-servers/{name}``  remove one

Per-server ``ETag`` / ``If-Match`` (and ``If-None-Match: *`` for
create-only PUT) gives optimistic concurrency at the right granularity:
concurrent edits to *different* servers stop conflicting at all;
concurrent edits to the *same* server get a clean 412 with the current
ETag echoed back.

ACP variant: ``ACPAgentSettings`` has no ``mcp_config``. Read endpoints
on the missing collection return ``404``; writes return ``409`` with a
message pointing the caller at the agent-variant settings endpoint.

All writes still go through the file-locked ``store.update()``, so they
serialize with each other and with the global ``PATCH /api/settings`` —
this router does not introduce a separate persistence backend, just a
finer-grained API.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import ValidationError

from openhands.agent_server._secrets_exposure import (
    build_expose_context,
    get_config,
    parse_expose_secrets_header,
    translate_missing_cipher,
)
from openhands.agent_server.persistence import (
    PersistedSettings,
    get_settings_store,
)
from openhands.sdk.logger import get_logger
from openhands.sdk.settings import (
    MCPServerListResponse,
    MCPServerResponse,
    MCPServerSummary,
    OpenHandsAgentSettings,
)


logger = get_logger(__name__)

mcp_servers_router = APIRouter(tags=["MCP Servers"])

MCP_COLLECTION_PATH = "/settings/mcp-servers"
MCP_ITEM_PATH = "/settings/mcp-servers/{name}"

# MCP server names map 1:1 to dict keys in the underlying ``MCPConfig``;
# constrain to safe URL-path characters. Slashes are explicitly disallowed
# because they would collide with FastAPI's path-segment routing (a server
# called "@scope/server" would never match ``/mcp-servers/{name}``). Names
# stay 1–128 chars to bound on-disk size.
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]{1,128}$")


def _validate_server_name(name: str) -> None:
    if not _NAME_PATTERN.fullmatch(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid MCP server name. Use 1-128 characters from "
                "[A-Za-z0-9_.@:-]. Slashes are not allowed because the "
                "name is a single URL path segment."
            ),
        )


# ── Secret-walking (local to keep this router decoupled from settings.model) ─


def _walk_server_secret_values(server: dict[str, Any], transform) -> dict[str, Any]:
    """Return a copy of ``server`` with ``transform`` applied to every string
    value inside ``env`` / ``headers``. Mirrors the equivalent walker in
    ``openhands.sdk.settings.model`` but scoped to a single server so we
    don't have to build a synthetic ``MCPConfig`` wrapper around each
    response.
    """
    result = copy.deepcopy(server)
    for key in ("env", "headers"):
        mapping = result.get(key)
        if not isinstance(mapping, dict):
            continue
        result[key] = {
            k: (transform(v) if isinstance(v, str) else v) for k, v in mapping.items()
        }
    return result


# ── ETag computation ──────────────────────────────────────────────────────


def _compute_server_etag(server: dict[str, Any]) -> str:
    """ETag for a single MCP server config.

    Computed over a **plaintext-canonical** JSON projection of the server's
    config (sorted keys, no whitespace). Crucially this is *not* a hash of
    on-disk bytes — those go through Fernet, whose nonce changes every save,
    which would make identical-state writes look different and defeat
    idempotency.
    """
    canonical = json.dumps(server, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
    return f'"{digest}"'


def _parse_if_match(header_value: str | None) -> str | None:
    """Return the (still-quoted) ETag value from an ``If-Match`` header, or
    ``None`` if the header is absent. ``"*"`` is returned verbatim and means
    "any current state is acceptable, but the resource must exist"."""
    if header_value is None:
        return None
    return header_value.strip()


def _check_preconditions(
    current_etag: str,
    *,
    resource_exists: bool,
    if_match: str | None,
    if_none_match: str | None,
) -> None:
    """Apply ``If-Match`` / ``If-None-Match`` precondition checks.

    * ``If-Match: <etag>``      → 412 unless ``<etag>`` equals the current.
    * ``If-Match: *``           → 412 if the resource does not exist.
    * ``If-None-Match: *``      → 412 if the resource *does* exist
                                  (create-only PUT semantics).
    * ``If-None-Match: <etag>`` → 412 if ``<etag>`` equals the current
                                  (used by GETs for cache validation; we
                                  accept the header for write endpoints
                                  too for symmetry, treating any match as
                                  a precondition failure).

    On failure, raises ``412 Precondition Failed`` with the current ETag in
    the ``ETag`` response header so the client can retry against the live
    state. On a missing resource, raises ``412`` as well (still semantically
    correct: the precondition failed because the resource isn't there to
    match against).
    """
    if if_match is not None:
        if if_match == "*":
            if not resource_exists:
                raise HTTPException(
                    status_code=status.HTTP_412_PRECONDITION_FAILED,
                    detail=(
                        "If-Match: * requires the resource to exist, "
                        "but no MCP server with that name was found."
                    ),
                )
        elif if_match != current_etag:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=(
                    "If-Match does not match the current ETag. Re-fetch "
                    "GET /api/settings/mcp-servers/{name} and retry."
                ),
                headers={"ETag": current_etag} if resource_exists else None,
            )

    if if_none_match is not None:
        if if_none_match == "*":
            if resource_exists:
                raise HTTPException(
                    status_code=status.HTTP_412_PRECONDITION_FAILED,
                    detail=(
                        "If-None-Match: * requires the resource to not "
                        "exist, but an MCP server with that name already "
                        "does."
                    ),
                    headers={"ETag": current_etag},
                )
        elif resource_exists and if_none_match == current_etag:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=(
                    "If-None-Match matched the current ETag. Re-fetch the "
                    "resource and retry."
                ),
                headers={"ETag": current_etag},
            )


# ── Settings → MCP servers extraction helpers ─────────────────────────────


def _ensure_openhands_variant(
    settings: PersistedSettings,
) -> OpenHandsAgentSettings:
    """Return ``settings.agent_settings`` if it is the OpenHands variant.

    The ACP variant has no ``mcp_config`` field — there is no per-server
    collection to manipulate. ``409`` signals the request is well-formed
    but the persisted resource is in an incompatible state; the message
    points the caller at the settings endpoint that *would* let them
    switch variants.
    """
    agent = settings.agent_settings
    if not isinstance(agent, OpenHandsAgentSettings):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "MCP servers are not supported by the current agent variant "
                f"({agent.agent_kind!r}). Switch to an OpenHands-variant "
                "agent via PATCH /api/settings before managing MCP servers."
            ),
        )
    return agent


def _dump_servers_dict(
    settings: PersistedSettings, *, expose_mode, cipher
) -> dict[str, dict[str, Any]]:
    """Dump ``mcp_config.mcpServers`` as a plain ``{name: dict}`` mapping.

    Goes through the model's ``mode="json"`` dump with the appropriate
    serialization context, so per-server ``env`` / ``headers`` are
    redacted / encrypted / plaintext exactly as for ``GET /api/settings``.
    """
    agent = settings.agent_settings
    context = build_expose_context(expose_mode, cipher)
    dumped = agent.model_dump(mode="json", context=context)
    mcp = dumped.get("mcp_config") or {}
    servers = mcp.get("mcpServers") or {}
    if not isinstance(servers, dict):
        return {}
    return servers


def _plaintext_server_or_404(
    settings: PersistedSettings, name: str, *, cipher
) -> dict[str, Any]:
    """Return the plaintext config for one server, or raise 404."""
    servers = _dump_servers_dict(settings, expose_mode="plaintext", cipher=cipher)
    server = servers.get(name)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No MCP server named {name!r} is configured.",
        )
    return server


def _server_summary(name: str, server: dict[str, Any]) -> MCPServerSummary:
    """Build a list-view summary from a server's dumped dict."""
    if "command" in server:
        kind = "stdio"
    elif "url" in server:
        kind = "remote"
    else:
        kind = "unknown"
    transport = server.get("transport")
    return MCPServerSummary(
        name=name,
        transport_kind=kind,
        transport=transport if isinstance(transport, str) else None,
        description=server.get("description"),
        icon=server.get("icon"),
    )


def _validate_servers_dict(
    servers: dict[str, dict[str, Any]], *, source_label: str
) -> dict[str, Any]:
    """Re-validate the (mutated) ``mcpServers`` dict by passing it through
    ``OpenHandsAgentSettings`` so all model invariants (including
    cross-server ones from ``MCPConfig``) are checked. Returns the merged
    plaintext ``mcp_config`` payload ready to assign back to
    ``agent_settings``.

    Sanitizes validation errors to avoid leaking secret values that may
    appear in the input dict.
    """
    payload = {"mcp_config": {"mcpServers": servers}}
    try:
        # We only need the field to round-trip; the rest of the agent
        # settings come from the live in-memory ``agent_settings``.
        OpenHandsAgentSettings.model_validate(
            payload,
            context={"expose_secrets": "plaintext"},
            from_attributes=False,
        )
    except ValidationError as exc:
        # Strip ``input`` from the error reports to avoid echoing secret
        # values back. The location + message are still informative.
        errors = [
            {"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"Invalid MCP server config ({source_label}).",
                "errors": errors,
            },
        ) from exc
    return payload["mcp_config"]


# ── Endpoints ─────────────────────────────────────────────────────────────


@mcp_servers_router.get(MCP_COLLECTION_PATH, response_model=MCPServerListResponse)
async def list_mcp_servers(request: Request) -> MCPServerListResponse:
    """List MCP servers as summaries (no ``env`` or ``headers``).

    Returns an empty list when the persisted variant is ACP — list views
    are non-modifying so the more permissive shape (rather than 409) keeps
    polling clients simple.
    """
    config = get_config(request)
    store = get_settings_store(config)
    settings = store.load() or PersistedSettings()
    agent = settings.agent_settings
    if not isinstance(agent, OpenHandsAgentSettings):
        return MCPServerListResponse(servers=[])

    # List view: use ``"plaintext"`` so we can inspect ``description`` /
    # ``icon`` / ``transport`` directly; we explicitly do *not* include
    # ``env`` or ``headers`` in the response shape regardless of mode.
    with translate_missing_cipher():
        servers = _dump_servers_dict(
            settings, expose_mode="plaintext", cipher=config.cipher
        )
    summaries = [_server_summary(n, s) for n, s in sorted(servers.items())]
    return MCPServerListResponse(servers=summaries)


@mcp_servers_router.get(MCP_ITEM_PATH, response_model=MCPServerResponse)
async def get_mcp_server(request: Request, name: str) -> Response:
    """Read one MCP server's full configuration.

    Honours ``X-Expose-Secrets`` exactly like ``GET /api/settings``:

    * absent (default): ``env``/``headers`` values are redacted
    * ``encrypted``: Fernet-encrypted ciphertext
    * ``plaintext``: raw secret values

    Emits an ``ETag`` header bound to this server's plaintext-canonical
    config so write endpoints can use ``If-Match`` to detect concurrent
    edits to *this server specifically* (without conflicting with edits
    to other servers).
    """
    _validate_server_name(name)
    expose_mode = parse_expose_secrets_header(request)
    config = get_config(request)
    store = get_settings_store(config)
    settings = store.load() or PersistedSettings()
    agent = settings.agent_settings
    if not isinstance(agent, OpenHandsAgentSettings):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "MCP servers are not configured (current agent variant has "
                "no MCP support)."
            ),
        )

    # ETag is always derived from the plaintext state so it's stable across
    # different ``X-Expose-Secrets`` requests for the same logical content.
    plaintext_server = _plaintext_server_or_404(settings, name, cipher=config.cipher)
    etag = _compute_server_etag(plaintext_server)

    # Build the response body with the requested exposure mode.
    if expose_mode is None:
        # Redact secrets for the default mode.
        response_server = _walk_server_secret_values(
            plaintext_server, lambda _v: "[REDACTED]"
        )
    elif expose_mode == "plaintext":
        response_server = plaintext_server
    else:
        # ``encrypted``: dump again with that mode so the model's serializer
        # runs through its Fernet path.
        with translate_missing_cipher():
            servers = _dump_servers_dict(
                settings, expose_mode="encrypted", cipher=config.cipher
            )
        response_server = servers[name]

    client_host = request.client.host if request.client else "unknown"
    log_extra = {"client_host": client_host, "expose_mode": expose_mode or "redacted"}
    if expose_mode == "plaintext":
        logger.warning(
            "MCP server %r accessed with PLAINTEXT secrets",
            name,
            extra=log_extra,
        )
    else:
        logger.info("MCP server %r accessed", name, extra=log_extra)

    payload = MCPServerResponse(name=name, config=response_server)
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        headers={"ETag": etag},
    )


@mcp_servers_router.put(MCP_ITEM_PATH, response_model=MCPServerResponse)
async def upsert_mcp_server(
    request: Request, name: str, server: dict[str, Any]
) -> Response:
    """Create or replace an MCP server.

    Body is the raw ``fastmcp`` server config (the value of
    ``MCPConfig.mcpServers[name]``). The discriminator is implicit
    (``command``-bearing → stdio, ``url``-bearing → remote) — fastmcp's
    own validators pick the variant; this endpoint just passes through.

    Preconditions:

    * ``If-Match: <etag>`` succeeds only if the named server currently
      has that ETag (concurrent-edit detection).
    * ``If-Match: *`` requires the server to already exist (update-only).
    * ``If-None-Match: *`` requires the server to *not* exist (create-only).

    Returns the new resource state (with secrets redacted by default; the
    caller can re-fetch with ``X-Expose-Secrets`` if they need the values
    in encrypted/plaintext form) and the new ``ETag``.
    """
    _validate_server_name(name)
    config = get_config(request)
    store = get_settings_store(config)
    if_match = _parse_if_match(request.headers.get("If-Match"))
    if_none_match = _parse_if_match(request.headers.get("If-None-Match"))

    created = False

    def apply(settings: PersistedSettings) -> PersistedSettings:
        nonlocal created
        agent = _ensure_openhands_variant(settings)
        servers = _dump_servers_dict(
            settings, expose_mode="plaintext", cipher=config.cipher
        )
        existing = servers.get(name)
        current_etag = _compute_server_etag(existing) if existing is not None else ""
        _check_preconditions(
            current_etag,
            resource_exists=existing is not None,
            if_match=if_match,
            if_none_match=if_none_match,
        )

        servers[name] = server
        new_mcp = _validate_servers_dict(servers, source_label=f"server {name!r}")

        agent_dump = agent.model_dump(
            mode="json",
            context={"expose_secrets": "plaintext", "cipher": config.cipher},
        )
        agent_dump["mcp_config"] = new_mcp
        with translate_missing_cipher():
            new_agent = OpenHandsAgentSettings.model_validate(
                agent_dump,
                context={"expose_secrets": "plaintext", "cipher": config.cipher},
            )
        settings.agent_settings = new_agent
        created = existing is None
        return settings

    try:
        new_settings = store.update(apply)
    except HTTPException:
        raise
    except RuntimeError as exc:
        # Corrupted-store or cipher-mismatch path, mirroring settings_router.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Settings store is corrupted or unreadable: {exc}",
        ) from exc

    # Return the new state with redacted secrets (default) + new ETag.
    plaintext = _plaintext_server_or_404(new_settings, name, cipher=config.cipher)
    etag = _compute_server_etag(plaintext)
    redacted = _walk_server_secret_values(plaintext, lambda _v: "[REDACTED]")
    payload = MCPServerResponse(name=name, config=redacted)
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        status_code=(status.HTTP_201_CREATED if created else status.HTTP_200_OK),
        headers={"ETag": etag},
    )


@mcp_servers_router.patch(MCP_ITEM_PATH, response_model=MCPServerResponse)
async def patch_mcp_server(
    request: Request, name: str, patch: dict[str, Any]
) -> Response:
    """Partial update of an existing MCP server.

    Only the keys present in ``patch`` are modified. ``env`` and
    ``headers`` are *replaced* wholesale at the top level (their values
    are dicts; if you want to remove one entry, send the new map without
    it) — this matches Pydantic's per-field replace semantics and avoids
    ambiguity with "is this value being cleared or just absent?".

    Returns 404 if no server with that name exists (use PUT to create).
    """
    _validate_server_name(name)
    config = get_config(request)
    store = get_settings_store(config)
    if_match = _parse_if_match(request.headers.get("If-Match"))
    if_none_match = _parse_if_match(request.headers.get("If-None-Match"))

    def apply(settings: PersistedSettings) -> PersistedSettings:
        agent = _ensure_openhands_variant(settings)
        servers = _dump_servers_dict(
            settings, expose_mode="plaintext", cipher=config.cipher
        )
        existing = servers.get(name)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No MCP server named {name!r}; PATCH cannot create. "
                    "Use PUT instead."
                ),
            )
        _check_preconditions(
            _compute_server_etag(existing),
            resource_exists=True,
            if_match=if_match,
            if_none_match=if_none_match,
        )

        merged = {**existing, **patch}
        servers[name] = merged
        new_mcp = _validate_servers_dict(servers, source_label=f"server {name!r}")

        agent_dump = agent.model_dump(
            mode="json",
            context={"expose_secrets": "plaintext", "cipher": config.cipher},
        )
        agent_dump["mcp_config"] = new_mcp
        with translate_missing_cipher():
            new_agent = OpenHandsAgentSettings.model_validate(
                agent_dump,
                context={"expose_secrets": "plaintext", "cipher": config.cipher},
            )
        settings.agent_settings = new_agent
        return settings

    try:
        new_settings = store.update(apply)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Settings store is corrupted or unreadable: {exc}",
        ) from exc

    plaintext = _plaintext_server_or_404(new_settings, name, cipher=config.cipher)
    etag = _compute_server_etag(plaintext)
    redacted = _walk_server_secret_values(plaintext, lambda _v: "[REDACTED]")
    payload = MCPServerResponse(name=name, config=redacted)
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        headers={"ETag": etag},
    )


@mcp_servers_router.delete(MCP_ITEM_PATH, status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(request: Request, name: str) -> Response:
    """Remove one MCP server.

    Honours ``If-Match`` to guard against deleting a server that has been
    re-created or modified by another client since the caller last viewed
    it. Returns 404 (idempotent in the sense that re-deleting a missing
    server is reported as such; we don't silently 204 on absence so the
    client can tell whether their delete actually removed anything).
    """
    _validate_server_name(name)
    config = get_config(request)
    store = get_settings_store(config)
    if_match = _parse_if_match(request.headers.get("If-Match"))
    if_none_match = _parse_if_match(request.headers.get("If-None-Match"))

    def apply(settings: PersistedSettings) -> PersistedSettings:
        agent = _ensure_openhands_variant(settings)
        servers = _dump_servers_dict(
            settings, expose_mode="plaintext", cipher=config.cipher
        )
        existing = servers.get(name)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No MCP server named {name!r} to delete.",
            )
        _check_preconditions(
            _compute_server_etag(existing),
            resource_exists=True,
            if_match=if_match,
            if_none_match=if_none_match,
        )

        del servers[name]
        new_mcp = _validate_servers_dict(servers, source_label="after delete")
        agent_dump = agent.model_dump(
            mode="json",
            context={"expose_secrets": "plaintext", "cipher": config.cipher},
        )
        agent_dump["mcp_config"] = new_mcp
        with translate_missing_cipher():
            new_agent = OpenHandsAgentSettings.model_validate(
                agent_dump,
                context={"expose_secrets": "plaintext", "cipher": config.cipher},
            )
        settings.agent_settings = new_agent
        return settings

    try:
        store.update(apply)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Settings store is corrupted or unreadable: {exc}",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["mcp_servers_router"]
