"""Static asset exposure tests."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from heartbeat.server import config as server_config
from heartbeat.server.main import create_app

API_KEY = "test-api-key"
WEBP_BYTES = b"RIFFfake"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Build a TestClient app rooted at a temp data dir holding private files."""
    monkeypatch.setenv("HEARTBEAT_API_KEY", API_KEY)
    monkeypatch.setenv("HEARTBEAT_DATA_DIR", str(tmp_path))
    server_config.reset_settings()
    (tmp_path / "secrets.json").write_text('{"api_key": "secret"}', encoding="utf-8")
    snapshots = tmp_path / "snapshots"
    snapshots.mkdir()
    (snapshots / "desktop-latest.webp").write_bytes(WEBP_BYTES)
    (snapshots / "desktop-latest.meta.json").write_text("{}", encoding="utf-8")
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    server_config.reset_settings()


def _assert_not_found(response: Response) -> None:
    """Assert the response is a protocol shaped 404."""
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_database_is_not_served(client: TestClient) -> None:
    """GET on the SQLite file is rejected."""
    _assert_not_found(client.get("/static/heartbeat.db"))


def test_secrets_file_is_not_served(client: TestClient) -> None:
    """GET on the secrets file is rejected."""
    _assert_not_found(client.get("/static/secrets.json"))


def test_wal_and_shm_sidecars_are_not_served(client: TestClient) -> None:
    """GET on SQLite sidecar files is rejected."""
    _assert_not_found(client.get("/static/heartbeat.db-wal"))
    _assert_not_found(client.get("/static/heartbeat.db-shm"))


def test_traversal_out_of_public_dir_is_rejected(client: TestClient) -> None:
    """GET with encoded traversal segments is rejected."""
    _assert_not_found(client.get("/static/snapshots/%2e%2e/%2e%2e/secrets.json"))


def test_metadata_sidecar_is_not_served(client: TestClient) -> None:
    """GET on snapshot metadata is rejected."""
    _assert_not_found(client.get("/static/snapshots/desktop-latest.meta.json"))


def test_static_root_is_not_listed(client: TestClient) -> None:
    """GET on the static prefix without a file is rejected."""
    _assert_not_found(client.get("/static/"))


def test_public_snapshot_is_served(client: TestClient) -> None:
    """GET on a snapshot image keeps working."""
    response = client.get("/static/snapshots/desktop-latest.webp")
    assert response.status_code == 200
    assert response.content == WEBP_BYTES


def test_public_cover_is_served(client: TestClient, tmp_path: Path) -> None:
    """GET on a cover image keeps working."""
    covers = tmp_path / "covers"
    covers.mkdir(exist_ok=True)
    (covers / "client.jpg").write_bytes(b"jpeg")
    assert client.get("/static/covers/client.jpg").status_code == 200


def test_docs_routes_are_disabled_by_default(client: TestClient) -> None:
    """GET on docs and schema routes is rejected when docs are off."""
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_docs_routes_open_when_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET on the schema route succeeds when the operator enables docs."""
    monkeypatch.setenv("HEARTBEAT_API_KEY", API_KEY)
    monkeypatch.setenv("HEARTBEAT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HEARTBEAT_DOCS_ENABLED", "true")
    server_config.reset_settings()
    app = create_app()
    with TestClient(app) as test_client:
        assert test_client.get("/openapi.json").status_code == 200
    server_config.reset_settings()
