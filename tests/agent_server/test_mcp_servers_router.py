"""Tests for the per-server MCP CRUD router.

Covers the win-list from the PR description:

* List / read / upsert / patch / delete a single server, without
  round-tripping every *other* server's encrypted secrets through the
  client.
* Per-server ETag is plaintext-canonical (idempotent across resaves).
* ``If-Match`` / ``If-None-Match`` give per-server optimistic concurrency:
  concurrent edits to *different* servers don't collide; concurrent edits
  to the *same* server get a clean 412 with the current ETag echoed.
* The ACP variant has no MCP collection — list returns empty, reads return
  404, writes return 409.
* ``X-Expose-Secrets`` is honoured on the per-server read.
* Adding a server through this router does not touch other servers'
  encrypted env/headers values on disk (the "splice locally" property).
"""

from __future__ import annotations

import os
import tempfile
from base64 import urlsafe_b64encode
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.agent_server.api import create_app
from openhands.agent_server.config import Config
from openhands.agent_server.persistence import reset_stores


@pytest.fixture
def temp_persistence_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        reset_stores()
        old_val = os.environ.get("OH_PERSISTENCE_DIR")
        os.environ["OH_PERSISTENCE_DIR"] = tmpdir
        yield Path(tmpdir)
        reset_stores()
        if old_val is not None:
            os.environ["OH_PERSISTENCE_DIR"] = old_val
        else:
            os.environ.pop("OH_PERSISTENCE_DIR", None)


@pytest.fixture
def secret_key():
    return urlsafe_b64encode(b"a" * 32).decode("ascii")


@pytest.fixture
def client(temp_persistence_dir, secret_key):
    config = Config(
        static_files_path=None,
        session_api_keys=[],
        secret_key=SecretStr(secret_key),
    )
    test_client = TestClient(create_app(config))
    # Seed the openhands variant by writing a minimal LLM config via the
    # legacy settings PATCH. (The router we're testing requires the
    # openhands variant; defaults already are openhands, but seeding a real
    # save makes the on-disk state deterministic for ETag assertions.)
    test_client.patch(
        "/api/settings",
        json={"agent_settings_diff": {"llm": {"model": "gpt-4"}}},
    )
    return test_client


# ── Helpers ────────────────────────────────────────────────────────────────


def _stdio_server(command: str = "echo", env: dict | None = None) -> dict:
    body: dict = {"command": command, "args": ["hello"]}
    if env is not None:
        body["env"] = env
    return body


def _remote_server(url: str = "http://example.com", headers=None) -> dict:
    body: dict = {"url": url}
    if headers is not None:
        body["headers"] = headers
    return body


# ── Listing ────────────────────────────────────────────────────────────────


def test_list_empty(client):
    response = client.get("/api/settings/mcp-servers")
    assert response.status_code == 200
    assert response.json() == {"servers": []}


def test_list_after_creates(client):
    client.put(
        "/api/settings/mcp-servers/local",
        json=_stdio_server(command="python", env={"K": "v"}),
    )
    client.put(
        "/api/settings/mcp-servers/remote",
        json=_remote_server(headers={"Authorization": "Bearer x"}),
    )
    response = client.get("/api/settings/mcp-servers")
    assert response.status_code == 200
    names = [s["name"] for s in response.json()["servers"]]
    kinds = {s["name"]: s["transport_kind"] for s in response.json()["servers"]}
    assert names == ["local", "remote"]  # sorted
    assert kinds == {"local": "stdio", "remote": "remote"}


def test_list_never_contains_secrets(client):
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"TOKEN": "super-secret"}),
    )
    response = client.get("/api/settings/mcp-servers")
    body = response.json()
    # Summary shape is fixed — no env/headers at all.
    server = body["servers"][0]
    assert set(server) == {
        "name",
        "transport_kind",
        "transport",
        "description",
        "icon",
    }


# ── Read one ───────────────────────────────────────────────────────────────


def test_get_one_redacted_by_default(client):
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"TOKEN": "super-secret"}),
    )
    response = client.get("/api/settings/mcp-servers/x")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "x"
    assert body["config"]["env"] == {"TOKEN": "[REDACTED]"}
    assert response.headers["ETag"].startswith('"')


def test_get_one_plaintext_via_header(client):
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"TOKEN": "super-secret"}),
    )
    response = client.get(
        "/api/settings/mcp-servers/x",
        headers={"X-Expose-Secrets": "plaintext"},
    )
    assert response.json()["config"]["env"] == {"TOKEN": "super-secret"}


def test_get_one_encrypted_via_header(client):
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"TOKEN": "super-secret"}),
    )
    response = client.get(
        "/api/settings/mcp-servers/x",
        headers={"X-Expose-Secrets": "encrypted"},
    )
    encrypted_value = response.json()["config"]["env"]["TOKEN"]
    assert encrypted_value.startswith("gAAAAA")  # Fernet token prefix


def test_get_missing_returns_404(client):
    response = client.get("/api/settings/mcp-servers/nope")
    assert response.status_code == 404


def test_get_invalid_name_returns_400(client):
    response = client.get("/api/settings/mcp-servers/has spaces")
    # FastAPI routes accept the path; our validator rejects it.
    assert response.status_code == 400


# ── ETag stability and change ─────────────────────────────────────────────


def test_etag_stable_across_identical_resaves(client):
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v"}),
    )
    etag1 = client.get("/api/settings/mcp-servers/x").headers["ETag"]

    # Re-PUT the exact same body. The on-disk Fernet ciphertext for ``K``
    # changes (per-save nonce), but the *plaintext-canonical* state is
    # identical, so the ETag must not move.
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v"}),
    )
    etag2 = client.get("/api/settings/mcp-servers/x").headers["ETag"]
    assert etag1 == etag2


def test_etag_changes_on_real_change(client):
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v"}),
    )
    etag1 = client.get("/api/settings/mcp-servers/x").headers["ETag"]

    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v2"}),
    )
    etag2 = client.get("/api/settings/mcp-servers/x").headers["ETag"]
    assert etag1 != etag2


# ── Optimistic concurrency ─────────────────────────────────────────────────


def test_put_with_matching_if_match_succeeds(client):
    client.put("/api/settings/mcp-servers/x", json=_stdio_server(env={"K": "v"}))
    etag = client.get("/api/settings/mcp-servers/x").headers["ETag"]
    response = client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v2"}),
        headers={"If-Match": etag},
    )
    assert response.status_code == 200
    assert response.headers["ETag"] != etag


def test_put_with_stale_if_match_returns_412(client):
    client.put("/api/settings/mcp-servers/x", json=_stdio_server(env={"K": "v"}))
    etag = client.get("/api/settings/mcp-servers/x").headers["ETag"]
    # Another client mutates first.
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "vA"}),
    )
    response = client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "vB"}),
        headers={"If-Match": etag},
    )
    assert response.status_code == 412
    # The current ETag is echoed so the client can rebase + retry.
    assert response.headers["ETag"] != etag


def test_put_if_none_match_star_creates_when_absent(client):
    response = client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v"}),
        headers={"If-None-Match": "*"},
    )
    assert response.status_code == 201


def test_put_if_none_match_star_rejects_when_exists(client):
    client.put("/api/settings/mcp-servers/x", json=_stdio_server(env={"K": "v"}))
    response = client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v2"}),
        headers={"If-None-Match": "*"},
    )
    assert response.status_code == 412
    # Current ETag is echoed for the client to choose to PUT-update.
    assert response.headers["ETag"].startswith('"')


def test_put_if_match_star_rejects_when_absent(client):
    response = client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v"}),
        headers={"If-Match": "*"},
    )
    assert response.status_code == 412


def test_concurrent_edits_to_different_servers_dont_conflict(client):
    """The headline win: per-server ETag means two clients each adding a
    different server can both proceed using their own If-Match, without
    one of them having to retry. This is the failure mode the global
    settings PATCH cannot avoid."""
    # Client A's view: empty.
    # Client B's view: empty.
    a = client.put(
        "/api/settings/mcp-servers/server-a",
        json=_stdio_server(),
        headers={"If-None-Match": "*"},
    )
    b = client.put(
        "/api/settings/mcp-servers/server-b",
        json=_stdio_server(),
        headers={"If-None-Match": "*"},
    )
    assert a.status_code == 201
    assert b.status_code == 201

    response = client.get("/api/settings/mcp-servers")
    assert [s["name"] for s in response.json()["servers"]] == [
        "server-a",
        "server-b",
    ]


def test_concurrent_edits_to_same_server_one_wins(client):
    """Same-server collision: the second writer's stale If-Match fails
    explicitly rather than silently overwriting."""
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"VERSION": "1"}),
    )
    shared_etag = client.get("/api/settings/mcp-servers/x").headers["ETag"]

    a = client.patch(
        "/api/settings/mcp-servers/x",
        json={"env": {"VERSION": "2"}},
        headers={"If-Match": shared_etag},
    )
    assert a.status_code == 200

    b = client.patch(
        "/api/settings/mcp-servers/x",
        json={"env": {"VERSION": "3"}},
        headers={"If-Match": shared_etag},  # stale
    )
    assert b.status_code == 412

    # Only A's write landed.
    after = client.get(
        "/api/settings/mcp-servers/x",
        headers={"X-Expose-Secrets": "plaintext"},
    )
    assert after.json()["config"]["env"]["VERSION"] == "2"


# ── PATCH ──────────────────────────────────────────────────────────────────


def test_patch_partial_keeps_unsent_fields(client):
    client.put(
        "/api/settings/mcp-servers/x",
        json={
            "command": "python",
            "args": ["server.py"],
            "env": {"K": "v"},
            "description": "important",
        },
    )

    # Patch only env.
    response = client.patch(
        "/api/settings/mcp-servers/x",
        json={"env": {"K": "v2"}},
    )
    assert response.status_code == 200

    after = client.get(
        "/api/settings/mcp-servers/x",
        headers={"X-Expose-Secrets": "plaintext"},
    ).json()["config"]
    assert after["command"] == "python"  # preserved
    assert after["args"] == ["server.py"]  # preserved
    assert after["description"] == "important"  # preserved
    assert after["env"] == {"K": "v2"}  # updated


def test_patch_on_missing_server_returns_404(client):
    response = client.patch("/api/settings/mcp-servers/nope", json={"description": "x"})
    assert response.status_code == 404


def test_patch_invalid_body_returns_422(client):
    client.put("/api/settings/mcp-servers/x", json=_stdio_server())
    # ``timeout`` is typed as a number — string fails fastmcp validation.
    response = client.patch(
        "/api/settings/mcp-servers/x",
        json={"timeout": "not-a-number"},
    )
    assert response.status_code == 422


# ── DELETE ─────────────────────────────────────────────────────────────────


def test_delete_existing_returns_204(client):
    client.put("/api/settings/mcp-servers/x", json=_stdio_server())
    response = client.delete("/api/settings/mcp-servers/x")
    assert response.status_code == 204
    # Subsequent GET is 404.
    assert client.get("/api/settings/mcp-servers/x").status_code == 404


def test_delete_missing_returns_404(client):
    response = client.delete("/api/settings/mcp-servers/nope")
    assert response.status_code == 404


def test_delete_with_stale_if_match_returns_412(client):
    client.put(
        "/api/settings/mcp-servers/x",
        json=_stdio_server(env={"K": "v"}),
    )
    etag = client.get("/api/settings/mcp-servers/x").headers["ETag"]
    # Move the server forward.
    client.patch("/api/settings/mcp-servers/x", json={"description": "changed"})
    response = client.delete("/api/settings/mcp-servers/x", headers={"If-Match": etag})
    assert response.status_code == 412
    # Server is still there.
    assert client.get("/api/settings/mcp-servers/x").status_code == 200


def test_delete_does_not_disturb_other_servers(client):
    client.put(
        "/api/settings/mcp-servers/keep",
        json=_stdio_server(env={"K": "v-keep"}),
    )
    client.put(
        "/api/settings/mcp-servers/drop",
        json=_stdio_server(env={"K": "v-drop"}),
    )
    client.delete("/api/settings/mcp-servers/drop")

    surviving = client.get(
        "/api/settings/mcp-servers/keep",
        headers={"X-Expose-Secrets": "plaintext"},
    ).json()
    assert surviving["config"]["env"]["K"] == "v-keep"


# ── ACP variant: no MCP collection ─────────────────────────────────────────


def _switch_to_acp(client):
    """Persist an ACP-variant agent_settings so the MCP endpoints have
    nothing to manipulate."""
    # Switching variants via the legacy diff replaces the whole
    # ``agent_settings`` via re-validation. We pass the variant
    # discriminator and minimum fields needed for ACPAgentSettings to
    # validate.
    response = client.patch(
        "/api/settings",
        json={
            "agent_settings_diff": {
                "agent_kind": "acp",
                "acp_server": "claude-code",
                "llm": {"model": "claude-sonnet-4-20250514"},
            }
        },
    )
    assert response.status_code == 200, response.text


def test_list_on_acp_variant_returns_empty(client):
    _switch_to_acp(client)
    response = client.get("/api/settings/mcp-servers")
    assert response.status_code == 200
    assert response.json() == {"servers": []}


def test_get_on_acp_variant_returns_404(client):
    _switch_to_acp(client)
    response = client.get("/api/settings/mcp-servers/x")
    assert response.status_code == 404


def test_put_on_acp_variant_returns_409(client):
    _switch_to_acp(client)
    response = client.put("/api/settings/mcp-servers/x", json=_stdio_server())
    assert response.status_code == 409
    assert "agent variant" in response.json()["detail"].lower()


def test_delete_on_acp_variant_returns_409(client):
    _switch_to_acp(client)
    response = client.delete("/api/settings/mcp-servers/x")
    assert response.status_code == 409


# ── "Splice locally" property: editing one server doesn't touch others ────


def test_editing_one_server_does_not_re_encrypt_others_on_change(client):
    """The conceptual win this router gives over the global settings PATCH:
    editing server B does not require the *client* to round-trip server A's
    secret values. (We can't directly observe what the client sent — but we
    can observe that the server preserved A's plaintext exactly through B's
    edit cycle, and the request to edit B didn't carry A's env at all.)
    """
    client.put(
        "/api/settings/mcp-servers/A",
        json=_stdio_server(env={"A_TOKEN": "alpha"}),
    )
    client.put(
        "/api/settings/mcp-servers/B",
        json=_stdio_server(env={"B_TOKEN": "beta"}),
    )

    # Edit B by name, sending *only* B's new env. (No A_TOKEN anywhere.)
    response = client.patch(
        "/api/settings/mcp-servers/B",
        json={"env": {"B_TOKEN": "beta-2"}},
    )
    assert response.status_code == 200

    a = client.get(
        "/api/settings/mcp-servers/A",
        headers={"X-Expose-Secrets": "plaintext"},
    ).json()
    b = client.get(
        "/api/settings/mcp-servers/B",
        headers={"X-Expose-Secrets": "plaintext"},
    ).json()
    assert a["config"]["env"] == {"A_TOKEN": "alpha"}
    assert b["config"]["env"] == {"B_TOKEN": "beta-2"}


# ── Name validation ───────────────────────────────────────────────────────


def test_invalid_name_rejected_on_write(client):
    response = client.put("/api/settings/mcp-servers/bad name", json=_stdio_server())
    assert response.status_code == 400


def test_valid_unusual_names_accepted(client):
    # Slashes are explicitly disallowed (single URL path segment); the
    # accepted set covers underscores, hyphens, dots, ``@``, and colons.
    for n in ["org_a", "github-mcp", "a.b.c", "@scope-server", "host:port"]:
        response = client.put(f"/api/settings/mcp-servers/{n}", json=_stdio_server())
        assert response.status_code in (200, 201), (n, response.text)


def test_slash_in_name_rejected_as_invalid(client):
    response = client.put(
        "/api/settings/mcp-servers/@scope/server", json=_stdio_server()
    )
    # FastAPI routes the trailing ``/server`` as the next path segment, so
    # the request never matches the route — 404 from the router itself.
    assert response.status_code == 404
