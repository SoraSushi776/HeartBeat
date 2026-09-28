"""SQLModel table definitions."""
from __future__ import annotations

from sqlmodel import Field, SQLModel


class Heartbeat(SQLModel, table=True):
    """Stored heartbeat snapshot row."""

    id: int | None = Field(default=None, primary_key=True)
    ts: int = Field(index=True)
    client_id: str = Field(index=True)
    payload_json: str = ""
    screenshot_path: str | None = None


class Diary(SQLModel, table=True):
    """Diary entry row."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    content: str = ""
    mood: str | None = None
    tags_json: str = "[]"
    created_ts: int = 0
    updated_ts: int = 0


class Friend(SQLModel, table=True):
    """Friend link row."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = ""
    url: str = ""
    avatar_url: str | None = None
    description: str | None = None
    sort: int = Field(default=0, index=True)


class Message(SQLModel, table=True):
    """Guestbook message row."""

    id: int | None = Field(default=None, primary_key=True)
    author: str = ""
    content: str = ""
    created_ts: int = Field(default=0, index=True)
    ip: str = Field(default="", index=True)
    location: str = ""
    expose_ip: bool = False


class MessageBan(SQLModel, table=True):
    """Banned guestbook IP row."""

    id: int | None = Field(default=None, primary_key=True)
    ip: str = Field(index=True)
    created_ts: int = 0


class IpLocationCache(SQLModel, table=True):
    """Cached IP geolocation row."""

    ip: str = Field(default="", primary_key=True)
    location: str = ""
    resolved_ts: int = 0


class GithubCache(SQLModel, table=True):
    """Single-row GitHub profile cache."""

    id: int | None = Field(default=None, primary_key=True)
    payload_json: str = "{}"
    fetched_ts: int = 0
