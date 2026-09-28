"""In-memory sliding window rate limiter for public write routes."""
from __future__ import annotations

import time
from collections import deque


class RateLimiter:
    """Track per-key request timestamps and enforce a sliding window cap."""

    _instance: RateLimiter | None = None

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}

    @classmethod
    def instance(cls) -> RateLimiter:
        """Return the process-wide limiter singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Drop the cached limiter singleton."""
        cls._instance = None

    def allow(self, key: str, limit: int, window_seconds: float) -> bool:
        """Record a hit for key and report whether it stays within limit."""
        now = time.monotonic()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] > window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True
