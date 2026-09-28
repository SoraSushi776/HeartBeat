"""Synchronous HTTP client for diary, friend and message v1 endpoints."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from heartbeat.protocol.models import API_PREFIX, HEADER_API_KEY

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Protocol-level API failure carrying a user-facing message."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class ApiSettings:
    """Connection settings for the diary and friend API."""

    base_url: str
    api_key: str
    timeout_seconds: float


class ApiService:
    """Diary and friend link CRUD over the v1 HTTP API."""

    def __init__(self, base_url: str, api_key: str, timeout_seconds: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds

    @classmethod
    def from_settings(cls, settings: ApiSettings) -> ApiService:
        """Build a service from connection settings."""
        return cls(settings.base_url, settings.api_key, settings.timeout_seconds)

    def list_diaries(self) -> dict[str, Any]:
        """Return the paged diary list payload."""
        return self._request("GET", "/diaries")

    def create_diary(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a diary entry and return the created row."""
        return self._request("POST", "/diaries", json=payload)

    def update_diary(self, diary_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """Patch a diary entry and return the updated row."""
        return self._request("PATCH", f"/diaries/{diary_id}", json=payload)

    def delete_diary(self, diary_id: int) -> dict[str, Any]:
        """Delete a diary entry and return the ack payload."""
        return self._request("DELETE", f"/diaries/{diary_id}")

    def list_friends(self) -> list[dict[str, Any]]:
        """Return all friend links ordered by sort weight."""
        return self._request("GET", "/friends")

    def create_friend(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a friend link and return the created row."""
        return self._request("POST", "/friends", json=payload)

    def update_friend(self, friend_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """Patch a friend link and return the updated row."""
        return self._request("PATCH", f"/friends/{friend_id}", json=payload)

    def delete_friend(self, friend_id: int) -> dict[str, Any]:
        """Delete a friend link and return the ack payload."""
        return self._request("DELETE", f"/friends/{friend_id}")

    def set_github_token(self, token: str, login: str = "") -> dict[str, Any]:
        """Push the GitHub PAT to the server for heatmap and README cache."""
        payload: dict[str, Any] = {"token": token}
        if login:
            payload["login"] = login
        return self._request("POST", "/github/token", json=payload)

    def list_messages(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """Return the paged guestbook message list payload."""
        return self._request("GET", f"/messages?limit={limit}&offset={offset}")

    def upload_background(self, data: bytes, content_type: str) -> dict[str, Any]:
        """Upload a site background image."""
        url = f"{self._base_url}{API_PREFIX}/background"
        try:
            response = httpx.put(
                url,
                content=data,
                headers={HEADER_API_KEY: self._api_key, "Content-Type": content_type},
                timeout=max(self._timeout, 30.0),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Background upload failed")
            raise ApiError(str(exc)) from exc
        body = response.json()
        if not isinstance(body, dict) or not body.get("ok"):
            raise ApiError(_error_message(body if isinstance(body, dict) else {}, response.status_code))
        return body.get("data") or {}

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}{API_PREFIX}{path}"
        try:
            response = httpx.request(
                method,
                url,
                json=json,
                headers={HEADER_API_KEY: self._api_key},
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning("API request failed: %s %s", method, path)
            raise ApiError(str(exc)) from exc
        try:
            body = response.json()
        except ValueError as exc:
            logger.warning("API response is not JSON: %s %s", method, path)
            raise ApiError(f"HTTP {response.status_code}") from exc
        if not isinstance(body, dict):
            raise ApiError(f"HTTP {response.status_code}")
        if body.get("ok"):
            return body.get("data")
        raise ApiError(_error_message(body, response.status_code))


def _error_message(body: dict[str, Any], status_code: int) -> str:
    error = body.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        return str(error["message"])
    return f"HTTP {status_code}"
