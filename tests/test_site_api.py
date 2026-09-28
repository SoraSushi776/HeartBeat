"""Site copy settings API tests."""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from heartbeat.server import config as server_config
from heartbeat.server.main import create_app

API = "/api/v1/site"
API_KEY = "test-api-key"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Build a TestClient app rooted at a temp data dir with a fixed API key."""
    monkeypatch.setenv("HEARTBEAT_API_KEY", API_KEY)
    monkeypatch.setenv("HEARTBEAT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HEARTBEAT_GITHUB_LOGIN", "")
    monkeypatch.setenv("HEARTBEAT_GITHUB_TOKEN", "")
    server_config.reset_settings()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    server_config.reset_settings()


def _auth() -> dict[str, str]:
    """Return the API key header for write requests."""
    return {"X-API-Key": API_KEY}


def test_get_site_defaults(client: TestClient) -> None:
    """GET returns default copy before any write."""
    response = client.get(API)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["title"] == "HeartBeat"
    assert body["data"]["tagline"] == "个人主页与实时状态"
    assert body["data"]["process_title"] == "TA的电脑上正在玩"


def test_put_site_requires_api_key(client: TestClient) -> None:
    """PUT rejects requests without a valid API key."""
    missing = client.put(API, json={"title": "X"})
    wrong = client.put(API, json={"title": "X"}, headers={"X-API-Key": "nope"})
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert missing.json()["error"]["code"] == "unauthorized"


def test_put_site_updates_and_persists(client: TestClient, tmp_path: Path) -> None:
    """PUT merges fields, persists them and GET reads them back."""
    response = client.put(
        API,
        json={"title": "Sora 的小站", "tagline": "记录生活", "process_title": "正在玩"},
        headers=_auth(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["title"] == "Sora 的小站"
    assert body["data"]["tagline"] == "记录生活"
    assert body["data"]["process_title"] == "正在玩"
    stored = json.loads((tmp_path / "secrets.json").read_text(encoding="utf-8"))
    assert stored["site"]["title"] == "Sora 的小站"
    assert client.get(API).json()["data"]["title"] == "Sora 的小站"


def test_put_site_partial_keeps_other_fields(client: TestClient) -> None:
    """PUT with a single field leaves the remaining fields unchanged."""
    client.put(API, json={"title": "A", "tagline": "B", "process_title": "C"}, headers=_auth())
    response = client.put(API, json={"tagline": "B2"}, headers=_auth())
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "A"
    assert data["tagline"] == "B2"
    assert data["process_title"] == "C"


def test_put_site_rejects_blank_title(client: TestClient) -> None:
    """PUT rejects an empty or whitespace-only title."""
    response = client.put(API, json={"title": "   "}, headers=_auth())
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_payload"


def test_put_site_rejects_overlong_title(client: TestClient) -> None:
    """PUT rejects a title longer than 80 characters."""
    response = client.put(API, json={"title": "x" * 81}, headers=_auth())
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_payload"
