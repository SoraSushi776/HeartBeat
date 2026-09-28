"""GitHub cache API and sanitizer tests."""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from heartbeat.server import config as server_config
from heartbeat.server.db import create_session
from heartbeat.server.main import create_app
from heartbeat.server.models import GithubCache
from heartbeat.server.services.github_cache import (
    GitHubCacheService,
    parse_contributions,
    parse_graphql_contributions,
)
from heartbeat.server.services.html_sanitize import sanitize_html

API = "/api/v1/github"
API_KEY = "test-api-key"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Build a TestClient app rooted at a temp data dir with a fixed API key."""
    monkeypatch.setenv("HEARTBEAT_API_KEY", API_KEY)
    monkeypatch.setenv("HEARTBEAT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HEARTBEAT_GITHUB_LOGIN", "")
    monkeypatch.setenv("HEARTBEAT_GITHUB_TOKEN", "")
    monkeypatch.setattr(GitHubCacheService, "refresh", lambda self: None)
    server_config.reset_settings()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    server_config.reset_settings()


def _auth() -> dict[str, str]:
    """Return the API key header for write requests."""
    return {"X-API-Key": API_KEY}


def test_get_github_empty_cache(client: TestClient) -> None:
    """GET returns an empty data object before the first refresh."""
    response = client.get(API)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"] == {}


def test_token_requires_api_key(client: TestClient) -> None:
    """POST /token rejects requests without a valid API key."""
    missing = client.post(f"{API}/token", json={"token": "ghp_x"})
    wrong = client.post(f"{API}/token", json={"token": "ghp_x"}, headers={"X-API-Key": "nope"})
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert missing.json()["error"]["code"] == "unauthorized"


def test_token_stores_secret(client: TestClient, tmp_path: Path) -> None:
    """POST /token persists the PAT into the secrets file and never echoes it."""
    response = client.post(f"{API}/token", json={"token": "ghp_secret"}, headers=_auth())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["configured"] is True
    assert body["data"]["updated_ts"] > 0
    assert "ghp_secret" not in response.text
    stored = json.loads((tmp_path / "secrets.json").read_text(encoding="utf-8"))
    assert stored["github_token"] == "ghp_secret"
    cache = client.get(API).json()
    assert "ghp_secret" not in json.dumps(cache)


def test_token_rejects_blank(client: TestClient) -> None:
    """POST /token rejects a blank token body."""
    response = client.post(f"{API}/token", json={"token": "   "}, headers=_auth())
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_payload"


def test_token_updates_login(client: TestClient) -> None:
    """POST /token optionally retargets the cached GitHub login."""
    response = client.post(
        f"{API}/token",
        json={"token": "ghp_secret", "login": "SoraSushi776"},
        headers=_auth(),
    )
    assert response.status_code == 200
    assert response.json()["data"]["login"] == "SoraSushi776"


def test_get_github_returns_cached_payload(client: TestClient) -> None:
    """GET serves the single cache row written by the background job."""
    client.post(f"{API}/token", json={"token": "ghp_secret", "login": "demo"}, headers=_auth())
    payload = {
        "login": "demo",
        "name": "Demo",
        "bio": "hello",
        "avatar_url": "https://example.com/a.png",
        "html_url": "https://github.com/demo",
        "readme_html": "<p>hi</p>",
        "contributions": {
            "total_last_year": 3,
            "days": [{"date": "2025-01-01", "count": 3, "level": 1}],
        },
        "fetched_ts": 1761648000000,
    }
    session = create_session()
    try:
        session.add(GithubCache(payload_json=json.dumps(payload), fetched_ts=payload["fetched_ts"]))
        session.commit()
    finally:
        session.close()
    body = client.get(API).json()
    assert body["ok"] is True
    assert body["data"]["login"] == "demo"
    assert body["data"]["contributions"]["days"][0]["level"] == 1


def test_sanitize_html_drops_scripts() -> None:
    """Sanitizer strips script tags, event handlers and javascript URLs."""
    dirty = (
        '<p onclick="x()">hi</p><script>alert(1)</script>'
        '<a href="javascript:alert(1)">bad</a>'
        '<a href="https://example.com">ok</a>'
        '<img src="x" onerror="alert(1)" alt="a">'
    )
    clean = sanitize_html(dirty)
    assert "script" not in clean.lower()
    assert "onclick" not in clean.lower()
    assert "onerror" not in clean.lower()
    assert "javascript:" not in clean.lower()
    assert 'href="https://example.com"' in clean
    assert "hi" in clean


def test_parse_graphql_contributions_levels() -> None:
    """GraphQL contribution levels map onto 0-4 heatmap buckets."""
    body = {
        "user": {
            "contributionsCollection": {
                "contributionCalendar": {
                    "totalContributions": 12,
                    "weeks": [
                        {
                            "contributionDays": [
                                {
                                    "date": "2025-01-01",
                                    "contributionCount": 4,
                                    "contributionLevel": "THIRD_QUARTILE",
                                },
                                {
                                    "date": "2025-01-02",
                                    "contributionCount": 0,
                                    "contributionLevel": "NONE",
                                },
                                {
                                    "date": "2025-01-03",
                                    "contributionCount": 9,
                                    "contributionLevel": "FOURTH_QUARTILE",
                                },
                            ]
                        }
                    ],
                }
            }
        }
    }
    parsed = parse_graphql_contributions(body)
    assert parsed["total_last_year"] == 12
    assert [day["level"] for day in parsed["days"]] == [3, 0, 4]
    assert [day["count"] for day in parsed["days"]] == [4, 0, 9]


def test_parse_contributions_html() -> None:
    """HTML calendar fallback still yields day levels and yearly total."""
    html = (
        '<td data-date="2025-01-01" data-level="2"></td>'
        '<td data-level="1" data-date="2025-01-02"></td>'
        "<h2>123 contributions in the last year</h2>"
    )
    parsed = parse_contributions(html)
    assert parsed["total_last_year"] == 123
    assert parsed["days"][0] == {"date": "2025-01-01", "count": 0, "level": 2}
