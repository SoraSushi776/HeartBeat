"""GitHub profile cache refresh service."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from sqlmodel import Session, select

from heartbeat.server.config import get_settings
from heartbeat.server.db import create_session
from heartbeat.server.models import GithubCache
from heartbeat.server.services.html_sanitize import sanitize_html
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

HTTP_TIMEOUT_S = 20.0
PROFILE_URL = "https://api.github.com/users/{login}"
README_URL = "https://api.github.com/repos/{login}/{login}/readme"
GRAPHQL_URL = "https://api.github.com/graphql"
CONTRIBUTIONS_URL = "https://github.com/users/{login}/contributions"
CONTRIBUTIONS_QUERY = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""
LEVEL_MAP: dict[str, int] = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}
DAY_PATTERN = re.compile(
    r'data-date="(?P<date>\d{4}-\d{2}-\d{2})"[^>]*data-level="(?P<level>\d)"[^>]*>'
    r"|data-level=\"(?P<level2>\d)\"[^>]*data-date=\"(?P<date2>\d{4}-\d{2}-\d{2})\"",
    re.IGNORECASE,
)
TOTAL_PATTERN = re.compile(r"(\d+)\s+contributions", re.IGNORECASE)


class GitHubCacheService:
    """Fetch GitHub profile, README and contributions into the cache table."""

    _instance: GitHubCacheService | None = None

    def __init__(self) -> None:
        self._client = httpx.Client(timeout=HTTP_TIMEOUT_S, follow_redirects=True)

    @classmethod
    def instance(cls) -> GitHubCacheService:
        """Return the process-wide GitHub cache service singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def refresh(self) -> None:
        """Fetch GitHub data and persist the cache row. Failures are logged only."""
        settings = get_settings()
        login = settings.github_login.strip()
        if not login:
            logger.debug("GitHub login not configured, cache refresh skipped")
            return
        try:
            payload = self._build_payload(login, settings.github_token.strip())
        except Exception:
            logger.exception("GitHub cache refresh failed for login=%s", login)
            return
        session = create_session()
        try:
            self._store(session, payload)
        finally:
            session.close()
        logger.info("GitHub cache refreshed for login=%s", login)

    def read(self, session: Session) -> dict[str, Any] | None:
        """Return the cached GitHub payload or None when empty."""
        row = session.exec(select(GithubCache)).first()
        if row is None:
            return None
        return json.loads(row.payload_json or "{}")

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _build_payload(self, login: str, token: str) -> dict[str, Any]:
        """Assemble the cache payload from GitHub endpoints."""
        profile = self._fetch_profile(login, token)
        readme_html = self._fetch_readme(login, token)
        contributions = self._fetch_contributions(login, token)
        return {
            "login": login,
            "name": profile.get("name"),
            "bio": profile.get("bio"),
            "avatar_url": profile.get("avatar_url"),
            "html_url": profile.get("html_url") or f"https://github.com/{login}",
            "readme_html": readme_html,
            "contributions": contributions,
            "fetched_ts": current_ms(),
        }

    def _fetch_profile(self, login: str, token: str) -> dict[str, Any]:
        """Fetch the GitHub user profile JSON."""
        response = self._client.get(PROFILE_URL.format(login=login), headers=_api_headers(token))
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def _fetch_readme(self, login: str, token: str) -> str:
        """Fetch the profile README rendered as sanitized HTML."""
        response = self._client.get(README_URL.format(login=login), headers=_readme_headers(token))
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        return sanitize_html(response.text)

    def _fetch_contributions(self, login: str, token: str) -> dict[str, Any]:
        """Fetch contribution days via GraphQL with PAT, else scrape the calendar page."""
        if token:
            return self._fetch_contributions_graphql(login, token)
        return self._fetch_contributions_html(login)

    def _fetch_contributions_graphql(self, login: str, token: str) -> dict[str, Any]:
        """Query contributionsCollection over GraphQL and map levels to 0-4."""
        response = self._client.post(
            GRAPHQL_URL,
            headers=_api_headers(token),
            json={"query": CONTRIBUTIONS_QUERY, "variables": {"login": login}},
        )
        response.raise_for_status()
        body = response.json()
        return parse_graphql_contributions(body if isinstance(body, dict) else {})

    def _fetch_contributions_html(self, login: str) -> dict[str, Any]:
        """Fetch and parse the public contribution calendar fragment."""
        response = self._client.get(CONTRIBUTIONS_URL.format(login=login))
        response.raise_for_status()
        return parse_contributions(response.text)

    def _store(self, session: Session, payload: dict[str, Any]) -> None:
        """Upsert the single GitHub cache row."""
        encoded = json.dumps(payload)
        fetched_ts = int(payload.get("fetched_ts", 0))
        row = session.exec(select(GithubCache)).first()
        if row is None:
            session.add(GithubCache(payload_json=encoded, fetched_ts=fetched_ts))
        else:
            row.payload_json = encoded
            row.fetched_ts = fetched_ts
            session.add(row)
        session.commit()


def refresh_github_cache() -> None:
    """Scheduled job entry that refreshes the GitHub cache."""
    GitHubCacheService.instance().refresh()


def parse_contributions(html: str) -> dict[str, Any]:
    """Parse contribution days and yearly total from GitHub calendar HTML."""
    days: list[dict[str, Any]] = []
    for match in DAY_PATTERN.finditer(html):
        date = match.group("date") or match.group("date2")
        level_raw = match.group("level") or match.group("level2") or "0"
        days.append({"date": date, "count": 0, "level": int(level_raw)})
    total = 0
    total_match = TOTAL_PATTERN.search(html)
    if total_match:
        total = int(total_match.group(1))
    return {"total_last_year": total, "days": days}


def parse_graphql_contributions(body: dict[str, Any]) -> dict[str, Any]:
    """Map a contributionsCollection GraphQL response into heatmap days."""
    root = body.get("data") if isinstance(body.get("data"), dict) else body
    user = (root or {}).get("user") or {}
    collection = user.get("contributionsCollection") or {}
    calendar = collection.get("contributionCalendar") or {}
    days: list[dict[str, Any]] = []
    for week in calendar.get("weeks") or []:
        for day in week.get("contributionDays") or []:
            level_name = str(day.get("contributionLevel") or "NONE").upper()
            days.append(
                {
                    "date": day.get("date") or "",
                    "count": int(day.get("contributionCount") or 0),
                    "level": LEVEL_MAP.get(level_name, 0),
                }
            )
    return {"total_last_year": int(calendar.get("totalContributions") or 0), "days": days}


def _api_headers(token: str) -> dict[str, str]:
    """Return headers for GitHub API calls, with bearer auth when a PAT exists."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "heartbeat-server"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _readme_headers(token: str) -> dict[str, str]:
    """Return headers requesting an HTML rendered README."""
    headers = {
        "Accept": "application/vnd.github.html",
        "User-Agent": "heartbeat-server",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers
