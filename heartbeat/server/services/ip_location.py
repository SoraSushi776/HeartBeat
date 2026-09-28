"""IP geolocation lookup with local cache for guestbook messages."""
from __future__ import annotations

import logging

import httpx
from sqlmodel import Session

from heartbeat.server.db import create_session
from heartbeat.server.models import IpLocationCache
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

LOOKUP_URL = "http://ip-api.com/json/{ip}"
LOOKUP_FIELDS = "status,country,countryCode,regionName"
LOOKUP_TIMEOUT_S = 4.0
UNKNOWN_LOCATION = "未知"
CHINA_CODE = "CN"


class IpLocationService:
    """Resolve IP addresses to display labels and cache the answers."""

    _instance: IpLocationService | None = None

    @classmethod
    def instance(cls) -> IpLocationService:
        """Return the process-wide geolocation singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Drop the cached geolocation singleton."""
        cls._instance = None

    def resolve(self, ip: str) -> str:
        """Return the cached or freshly looked-up location label for ip."""
        if not ip:
            return UNKNOWN_LOCATION
        session = create_session()
        try:
            cached = session.get(IpLocationCache, ip)
            if cached is not None and cached.location:
                return cached.location
            location = self._fetch(ip)
            self._store(session, ip, location)
            return location
        finally:
            session.close()

    def _fetch(self, ip: str) -> str:
        """Query the remote geolocation endpoint for one ip."""
        try:
            response = httpx.get(
                LOOKUP_URL.format(ip=ip),
                params={"fields": LOOKUP_FIELDS},
                timeout=LOOKUP_TIMEOUT_S,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            logger.warning("IP location lookup failed: %s", ip)
            return UNKNOWN_LOCATION
        return format_location(payload)

    def _store(self, session: Session, ip: str, location: str) -> None:
        """Persist a resolved location for ip into the cache table."""
        session.merge(IpLocationCache(ip=ip, location=location, resolved_ts=current_ms()))
        session.commit()


def format_location(payload: object) -> str:
    """Build the display label: province for CN, country otherwise."""
    data = payload if isinstance(payload, dict) else {}
    if str(data.get("status") or "") != "success":
        return UNKNOWN_LOCATION
    is_china = str(data.get("countryCode") or "") == CHINA_CODE
    province = str(data.get("regionName") or "")
    country = str(data.get("country") or "")
    label = province if is_china else country
    return label or UNKNOWN_LOCATION


def client_ip_from_headers(forwarded: str | None, fallback: str | None) -> str:
    """Pick the first X-Forwarded-For hop, else the direct client host."""
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return fallback or ""
