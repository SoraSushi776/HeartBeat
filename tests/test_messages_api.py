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
from heartbeat.server.services import ip_location as ip_location_module
from heartbeat.server.services.ip_location import format_location
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
    monkeypatch.setattr(
        ip_location_module.IpLocationService,
        "resolve",
        lambda self, ip: f"loc:{ip}",
    )
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


def test_create_records_ip_and_hides_it_from_public_list(client: TestClient) -> None:
    """POST stores the caller IP and the public list never exposes it."""
    _go_online()
    created = client.post(
        API,
        json={"content": "hello"},
        headers={"X-Forwarded-For": "203.0.113.9, 10.0.0.1"},
    )
    assert created.status_code == 200
    assert "ip" not in created.json()["data"]
    listing = client.get(API).json()["data"]
    item = listing["items"][0]
    assert "ip" not in item
    assert item["location"] is None


def test_expose_ip_gates_public_location(client: TestClient) -> None:
    """Public list returns location only when expose_ip is true."""
    _go_online()
    client.post(API, json={"content": "hidden", "expose_ip": False})
    client.post(API, json={"content": "shown", "expose_ip": True})
    listing = client.get(API).json()["data"]
    by_content = {item["content"]: item for item in listing["items"]}
    assert by_content["hidden"]["location"] is None
    assert by_content["shown"]["location"] == "loc:testclient"
    assert by_content["shown"]["expose_ip"] is True


def test_admin_list_exposes_ip_and_location(client: TestClient) -> None:
    """Admin list always returns IP and location and needs an API key."""
    _go_online()
    client.post(API, json={"content": "note"}, headers={"X-Forwarded-For": "198.51.100.4"})
    unauth = client.get(f"{API}/admin")
    assert unauth.status_code == 401
    listing = client.get(f"{API}/admin", headers={"X-API-Key": API_KEY}).json()["data"]
    item = listing["items"][0]
    assert item["ip"] == "198.51.100.4"
    assert item["location"] == "loc:198.51.100.4"
    assert item["content"] == "note"


def test_delete_message_requires_api_key(client: TestClient) -> None:
    """DELETE removes one message and rejects missing credentials."""
    _go_online()
    created = client.post(API, json={"content": "doomed"})
    message_id = created.json()["data"]["id"]
    assert client.delete(f"{API}/{message_id}").status_code == 401
    deleted = client.delete(f"{API}/{message_id}", headers={"X-API-Key": API_KEY})
    assert deleted.status_code == 200
    assert client.get(API).json()["data"]["total"] == 0
    missing = client.delete(f"{API}/{message_id}", headers={"X-API-Key": API_KEY})
    assert missing.status_code == 404


def test_ban_blocks_post_and_unban_restores(client: TestClient) -> None:
    """Banned IPs receive 403 until the ban row is removed."""
    _go_online()
    banned_ip = "203.0.113.50"
    ban = client.post(
        f"{API}/bans",
        json={"ip": banned_ip},
        headers={"X-API-Key": API_KEY},
    )
    assert ban.status_code == 200
    ban_id = ban.json()["data"]["id"]
    blocked = client.post(
        API,
        json={"content": "nope"},
        headers={"X-Forwarded-For": banned_ip},
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "forbidden"
    assert client.post(
        API,
        json={"content": "fine"},
        headers={"X-Forwarded-For": "198.51.100.7"},
    ).status_code == 200
    bans = client.get(f"{API}/bans", headers={"X-API-Key": API_KEY}).json()["data"]
    assert [row["ip"] for row in bans["items"]] == [banned_ip]
    unbanned = client.delete(f"{API}/bans/{ban_id}", headers={"X-API-Key": API_KEY})
    assert unbanned.status_code == 200
    restored = client.post(
        API,
        json={"content": "back"},
        headers={"X-Forwarded-For": banned_ip},
    )
    assert restored.status_code == 200


def test_ban_routes_require_api_key(client: TestClient) -> None:
    """Ban list and ban writes reject missing credentials."""
    assert client.get(f"{API}/bans").status_code == 401
    assert client.post(f"{API}/bans", json={"ip": "1.2.3.4"}).status_code == 401
    assert client.delete(f"{API}/bans/1").status_code == 401


def test_format_location_prefers_province_for_china() -> None:
    """Chinese IPs resolve to the province label, others to the country."""
    china = format_location(
        {"status": "success", "countryCode": "CN", "regionName": "广东", "country": "中国"}
    )
    assert china == "广东"
    abroad = format_location(
        {"status": "success", "countryCode": "JP", "regionName": "Tokyo", "country": "Japan"}
    )
    assert abroad == "Japan"
    assert format_location({"status": "fail"}) == "未知"
    assert format_location(None) == "未知"
