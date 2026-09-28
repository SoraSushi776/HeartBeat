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
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

HTTP_TIMEOUT_S = 20.0
PROFILE_URL = "https://api.github.com/users/{login}"
README_URL = "https://api.github.com/repos/{login}/{login}/readme"
CONTRIBUTIONS_URL = "https://github.com/users/{login}/contributions"
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
            payload = self._build_payload(login)
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

    def _build_payload(self, login: str) -> dict[str, Any]:
        """Assemble the cache payload from GitHub endpoints."""
        profile = self._fetch_profile(login)
        readme_html = self._fetch_readme(login)
        contributions = self._fetch_contributions(login)
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

    def _fetch_profile(self, login: str) -> dict[str, Any]:
        """Fetch the GitHub user profile JSON."""
        response = self._client.get(PROFILE_URL.format(login=login), headers=_api_headers())
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def _fetch_readme(self, login: str) -> str:
        """Fetch the profile README rendered as HTML."""
        response = self._client.get(README_URL.format(login=login), headers=_readme_headers())
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        return response.text

    def _fetch_contributions(self, login: str) -> dict[str, Any]:
        """Fetch and parse the contribution calendar fragment."""
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


def _api_headers() -> dict[str, str]:
    """Return headers for GitHub REST API calls."""
    return {"Accept": "application/vnd.github+json", "User-Agent": "heartbeat-server"}


def _readme_headers() -> dict[str, str]:
    """Return headers requesting an HTML rendered README."""
    return {
        "Accept": "application/vnd.github.html",
        "User-Agent": "heartbeat-server",
    }
