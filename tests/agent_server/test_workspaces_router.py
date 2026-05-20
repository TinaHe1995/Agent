"""Tests for workspaces_router endpoints.

Workspaces persisted on the agent-server (workspace/.openhands/workspaces.json)
replace the previous browser-local Zustand store, so every client connected to
the same server sees the same list. These tests cover the HTTP surface the
GUI consumes plus the file-locked persistence underneath it.
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from openhands.agent_server.api import create_app
from openhands.agent_server.config import Config
from openhands.agent_server.persistence import reset_stores


@pytest.fixture
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        reset_stores()
        monkeypatch.setenv("OH_PERSISTENCE_DIR", str(Path(tmpdir) / "persist"))
        config = Config(static_files_path=None, session_api_keys=[], secret_key=None)
        app = create_app(config)
        yield TestClient(app)
        reset_stores()


@pytest.fixture
def client_with_auth(monkeypatch):
    """Same as ``client`` but with ``session_api_keys`` configured so the
    ``/api`` header-only auth dependency is active. Used to prove that the
    workspaces router inherits the same auth as the rest of ``/api``.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        reset_stores()
        monkeypatch.setenv("OH_PERSISTENCE_DIR", str(Path(tmpdir) / "persist"))
        config = Config(
            static_files_path=None,
            session_api_keys=["test-key-123"],
            secret_key=None,
        )
        app = create_app(config)
        yield TestClient(app, raise_server_exceptions=False)
        reset_stores()


def test_list_workspaces_empty_when_no_file(client):
    # Act
    response = client.get("/api/workspaces")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"workspaces": [], "workspaceParents": []}


def test_add_workspaces_persists_camelcase_parent_path_and_dedupes_by_path(client):
    # Arrange
    payload = {
        "workspaces": [
            {"id": "/a", "name": "a", "path": "/a"},
            {
                "id": "/b",
                "name": "b",
                "path": "/b",
                "parentPath": "/parents/root",
            },
        ]
    }

    # Act: first add seeds the list; second add with an overlapping path is a no-op
    first = client.post("/api/workspaces", json=payload)
    second = client.post(
        "/api/workspaces",
        json={"workspaces": [{"id": "/a", "name": "a", "path": "/a"}]},
    )
    listed = client.get("/api/workspaces")

    # Assert
    assert first.status_code == 200
    assert second.status_code == 200
    assert listed.status_code == 200
    body = listed.json()
    assert [w["path"] for w in body["workspaces"]] == ["/a", "/b"]
    # camelCase wire format preserved — TS LocalWorkspace shape is unchanged.
    assert body["workspaces"][1]["parentPath"] == "/parents/root"


def test_delete_workspace_returns_404_when_path_absent(client):
    # Arrange
    client.post(
        "/api/workspaces",
        json={"workspaces": [{"id": "/a", "name": "a", "path": "/a"}]},
    )

    # Act
    removed_present = client.delete("/api/workspaces", params={"path": "/a"})
    removed_missing = client.delete("/api/workspaces", params={"path": "/nope"})
    remaining = client.get("/api/workspaces").json()

    # Assert
    assert removed_present.status_code == 200
    assert removed_present.json() == {"deleted": True}
    assert removed_missing.status_code == 404
    assert remaining["workspaces"] == []


def test_workspace_parents_add_and_remove_independent_of_workspaces(client):
    # Arrange: seed one workspace and one parent so we can prove they don't
    # collide when mutated independently.
    client.post(
        "/api/workspaces",
        json={"workspaces": [{"id": "/w", "name": "w", "path": "/w"}]},
    )

    # Act
    added = client.post(
        "/api/workspaces/parents",
        json={"parents": [{"id": "/p", "name": "p", "path": "/p"}]},
    )
    after_add = client.get("/api/workspaces").json()
    removed = client.delete("/api/workspaces/parents", params={"path": "/p"})
    missing = client.delete("/api/workspaces/parents", params={"path": "/p"})
    after_remove = client.get("/api/workspaces").json()

    # Assert
    assert added.status_code == 200
    assert [p["path"] for p in after_add["workspaceParents"]] == ["/p"]
    assert [w["path"] for w in after_add["workspaces"]] == ["/w"]
    assert removed.status_code == 200
    assert missing.status_code == 404
    assert after_remove["workspaceParents"] == []
    # Workspace survived the parent's removal.
    assert [w["path"] for w in after_remove["workspaces"]] == ["/w"]


def test_workspaces_survive_across_requests_via_disk_persistence(client):
    # Arrange: write something
    client.post(
        "/api/workspaces",
        json={"workspaces": [{"id": "/keep", "name": "keep", "path": "/keep"}]},
    )

    # Act: confirm it's on disk, then reset the in-memory singleton (simulating
    # a server restart) and re-read.
    persist_dir = Path(os.environ["OH_PERSISTENCE_DIR"])
    assert (persist_dir / "workspaces.json").exists()

    reset_stores()
    listed_again = client.get("/api/workspaces").json()

    # Assert
    assert [w["path"] for w in listed_again["workspaces"]] == ["/keep"]


def test_add_workspaces_dedupes_duplicate_paths_within_single_payload(client):
    """A single POST body with the same ``path`` twice must persist only once.

    Regression for the case where the dedupe set was computed from the
    pre-existing list only, so duplicates inside the incoming payload slipped
    through.
    """
    # Arrange
    payload = {
        "workspaces": [
            {"id": "first", "name": "first", "path": "/dup"},
            {"id": "second", "name": "second", "path": "/dup"},
        ]
    }

    # Act
    response = client.post("/api/workspaces", json=payload)
    listed = client.get("/api/workspaces")

    # Assert
    assert response.status_code == 200
    body = listed.json()
    assert [w["path"] for w in body["workspaces"]] == ["/dup"]
    # The first occurrence wins.
    assert body["workspaces"][0]["id"] == "first"


def test_add_workspace_parents_dedupes_duplicate_paths_within_single_payload(client):
    """Same dedupe contract for the ``/parents`` endpoint."""
    # Arrange
    payload = {
        "parents": [
            {"id": "first", "name": "first", "path": "/p"},
            {"id": "second", "name": "second", "path": "/p"},
        ]
    }

    # Act
    response = client.post("/api/workspaces/parents", json=payload)
    listed = client.get("/api/workspaces")

    # Assert
    assert response.status_code == 200
    body = listed.json()
    assert [p["path"] for p in body["workspaceParents"]] == ["/p"]
    assert body["workspaceParents"][0]["id"] == "first"


def test_list_workspaces_returns_409_when_persisted_file_is_corrupted(client):
    """A corrupted ``workspaces.json`` must NOT be silently masked as empty.

    Returning an empty list on corruption would let a subsequent POST
    overwrite the still-on-disk (potentially recoverable) data with defaults.
    """
    # Arrange: seed a real workspace, then clobber the file with garbage.
    client.post(
        "/api/workspaces",
        json={"workspaces": [{"id": "/a", "name": "a", "path": "/a"}]},
    )
    persist_dir = Path(os.environ["OH_PERSISTENCE_DIR"])
    (persist_dir / "workspaces.json").write_text("{not valid json", encoding="utf-8")
    # Force the next request to re-read from disk rather than the in-memory store.
    reset_stores()

    # Act
    response = client.get("/api/workspaces")

    # Assert
    assert response.status_code == 409
    assert "corrupt" in response.json()["detail"].lower()


# ── Auth ─────────────────────────────────────────────────────────────────
#
# The /api router applies a header-only ``X-Session-API-Key`` dependency when
# ``session_api_keys`` is configured. These tests prove the workspaces router
# inherits that gate — i.e. an unauthenticated client cannot read or mutate
# server-side workspace state.


def test_workspaces_endpoints_require_session_api_key_when_configured(
    client_with_auth,
):
    # Act: hit every state-changing endpoint plus GET without the header.
    no_header_get = client_with_auth.get("/api/workspaces")
    no_header_post = client_with_auth.post(
        "/api/workspaces",
        json={"workspaces": [{"id": "/a", "name": "a", "path": "/a"}]},
    )
    no_header_delete = client_with_auth.delete("/api/workspaces", params={"path": "/a"})
    no_header_parents_post = client_with_auth.post(
        "/api/workspaces/parents",
        json={"parents": [{"id": "/p", "name": "p", "path": "/p"}]},
    )
    no_header_parents_delete = client_with_auth.delete(
        "/api/workspaces/parents", params={"path": "/p"}
    )
    bad_header = client_with_auth.get(
        "/api/workspaces", headers={"X-Session-API-Key": "wrong-key"}
    )

    # Assert
    assert no_header_get.status_code == 401
    assert no_header_post.status_code == 401
    assert no_header_delete.status_code == 401
    assert no_header_parents_post.status_code == 401
    assert no_header_parents_delete.status_code == 401
    assert bad_header.status_code == 401


def test_workspaces_endpoints_accept_valid_session_api_key(client_with_auth):
    """A valid ``X-Session-API-Key`` lets the same endpoints serve normally."""
    # Arrange
    headers = {"X-Session-API-Key": "test-key-123"}

    # Act
    listed = client_with_auth.get("/api/workspaces", headers=headers)
    added = client_with_auth.post(
        "/api/workspaces",
        headers=headers,
        json={"workspaces": [{"id": "/a", "name": "a", "path": "/a"}]},
    )
    deleted = client_with_auth.delete(
        "/api/workspaces", headers=headers, params={"path": "/a"}
    )

    # Assert
    assert listed.status_code == 200
    assert added.status_code == 200
    assert deleted.status_code == 200
