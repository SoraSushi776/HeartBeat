"""Guestbook message API tests."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from heartbeat.server import config as server_config
from heartbeat.server.db import create_session, reset_engine
from heartbeat.server.main import create_app
from heartbeat.server.models import Heartbeat
from heartbeat.server.services.ratelimit import RateLimiter
from heartbeat.server.timeutil import current_ms

API = "/api/v1/messages"
API_KEY = "test-api-key"
CLIENT_ID = "desktop-main"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Build a TestClient app rooted at a temp data dir with a fixed API key."""
    monkeypatch.setenv("HEARTBEAT_API_KEY", API_KEY)
    monkeypatch.setenv("HEARTBEAT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HEARTBEAT_DEFAULT_CLIENT_ID", CLIENT_ID)
    server_config.reset_settings()
    reset_engine()
    RateLimiter.reset()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()
    server_config.reset_settings()
    RateLimiter.reset()


def _go_online(ts: int | None = None) -> None:
    """Insert a fresh heartbeat row so the online window accepts writes."""
    session = create_session()
    try:
        row = Heartbeat(
            ts=ts if ts is not None else current_ms(),
            client_id=CLIENT_ID,
            payload_json="{}",
        )
        session.add(row)
        session.commit()
    finally:
        session.close()


def test_list_empty(client: TestClient) -> None:
    """GET returns an empty paged list before any write."""
    response = client.get(API)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


def test_create_requires_content(client: TestClient) -> None:
    """POST rejects empty or whitespace-only content."""
    _go_online()
    for payload in ({"content": ""}, {"content": "   "}, {"author": "a"}):
        response = client.post(API, json=payload)
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_payload"


def test_create_rejects_when_offline(client: TestClient) -> None:
    """POST returns 409 while the client heartbeat is stale."""
    _go_online(ts=current_ms() - 10 * 60 * 1000)
    response = client.post(API, json={"content": "hello"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_create_and_list_roundtrip(client: TestClient) -> None:
    """POST stores the message and GET returns it newest first."""
    _go_online()
    created = client.post(API, json={"author": "Sora", "content": "hi there"})
    assert created.status_code == 200
    row = created.json()["data"]
    assert row["author"] == "Sora"
    assert row["content"] == "hi there"
    assert row["created_ts"] > 0
    anonymous = client.post(API, json={"content": "anon note"})
    assert anonymous.status_code == 200
    assert anonymous.json()["data"]["author"] == ""
    listing = client.get(f"{API}?limit=10&offset=0").json()["data"]
    assert listing["total"] == 2
    assert [item["content"] for item in listing["items"]] == ["anon note", "hi there"]


def test_create_normalizes_author(client: TestClient) -> None:
    """POST trims the author and falls back to an anonymous empty string."""
    _go_online()
    response = client.post(API, json={"author": "  Bob  ", "content": "yo"})
    assert response.status_code == 200
    assert response.json()["data"]["author"] == "Bob"


def test_rate_limit_blocks_flood(client: TestClient) -> None:
    """POST rejects writes past the sliding window cap."""
    _go_online()
    for _ in range(5):
        assert client.post(API, json={"content": "spam"}).status_code == 200
    response = client.post(API, json={"content": "spam"})
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
