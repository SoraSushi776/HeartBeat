"""Pydantic request and response models for the v1 protocol."""
from __future__ import annotations

from pydantic import Field, field_validator
from sqlmodel import SQLModel

from heartbeat.protocol.models import MediaState, Platform


class ClientPayload(SQLModel):
    """Client identity block."""

    id: str
    platform: Platform
    version: str = "0.1.0"


class SystemPayload(SQLModel):
    """Host load block."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    load_avg: list[float] = Field(default_factory=list)


class MediaPayload(SQLModel):
    """Now-playing block."""

    state: MediaState = MediaState.IDLE
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    app: str | None = None
    cover_url: str | None = None
    position_ms: int | None = None
    duration_ms: int | None = None


class ProcessPayload(SQLModel):
    """Running app block."""

    name: str
    count: int = 1


class PrivacyPayload(SQLModel):
    """Collection switches reported by client."""

    screenshot: bool = True
    media: bool = True
    processes: bool = True
    system: bool = True


class HeartbeatIn(SQLModel):
    """Heartbeat request body."""

    ts: int
    client: ClientPayload
    system: SystemPayload | None = None
    media: MediaPayload | None = None
    processes: list[ProcessPayload] = Field(default_factory=list)
    privacy: PrivacyPayload = Field(default_factory=PrivacyPayload)

    @field_validator("ts")
    @classmethod
    def ts_must_be_non_negative(cls, value: int) -> int:
        """Reject negative timestamps."""
        if value < 0:
            raise ValueError("ts must be non-negative UTC milliseconds")
        return value


class HeartbeatAccepted(SQLModel):
    """Heartbeat ack payload."""

    received_ts: int
    screenshot_upload_url: str | None = None
    screenshot_expires_in: int = 60


class ScreenshotStored(SQLModel):
    """Screenshot upload ack payload."""

    url: str
    ts: int


class ClientStatus(SQLModel):
    """Client identity inside status payload."""

    id: str
    platform: str
    version: str = ""


class ScreenshotStatus(SQLModel):
    """Latest snapshot descriptor inside status payload."""

    url: str
    ts: int
    width: int = 0
    height: int = 0


class StatusPayload(SQLModel):
    """Realtime status payload."""

    online: bool
    last_heartbeat_ts: int | None = None
    client: ClientStatus | None = None
    system: SystemPayload | None = None
    media: MediaPayload | None = None
    processes: list[ProcessPayload] = Field(default_factory=list)
    screenshot: ScreenshotStatus | None = None
    privacy: PrivacyPayload | None = None


class DiaryCreate(SQLModel):
    """Diary create body."""

    title: str = Field(max_length=200)
    content: str
    mood: str | None = None
    tags: list[str] = Field(default_factory=list)


class DiaryUpdate(SQLModel):
    """Diary partial update body."""

    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    mood: str | None = None
    tags: list[str] | None = None


class DiaryOut(SQLModel):
    """Diary response body."""

    id: int
    title: str
    content: str
    mood: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_ts: int = 0
    updated_ts: int = 0


class DiaryList(SQLModel):
    """Paged diary list payload."""

    items: list[DiaryOut] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0


class MessageCreate(SQLModel):
    """Guestbook create body."""

    author: str | None = Field(default=None, max_length=50)
    content: str
    expose_ip: bool = False

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        """Reject empty or whitespace-only content and cap its length."""
        text = value.strip()
        if not text:
            raise ValueError("content must not be empty")
        if len(text) > 500:
            raise ValueError("content must be at most 500 characters")
        return text


class MessageOut(SQLModel):
    """Guestbook message response body for the public list."""

    id: int
    author: str = ""
    content: str = ""
    created_ts: int = 0
    expose_ip: bool = False
    location: str | None = None


class MessageAdminOut(SQLModel):
    """Guestbook message response body for the admin client."""

    id: int
    author: str = ""
    content: str = ""
    created_ts: int = 0
    ip: str = ""
    location: str = ""
    expose_ip: bool = False


class MessageList(SQLModel):
    """Paged guestbook list payload."""

    items: list[MessageOut] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0


class MessageAdminList(SQLModel):
    """Paged guestbook list payload with IP details."""

    items: list[MessageAdminOut] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0


class BanCreate(SQLModel):
    """Guestbook IP ban create body."""

    ip: str = Field(min_length=1, max_length=64)


class BanOut(SQLModel):
    """Guestbook IP ban response body."""

    id: int
    ip: str = ""
    created_ts: int = 0


class BanList(SQLModel):
    """Guestbook IP ban list payload."""

    items: list[BanOut] = Field(default_factory=list)


class FriendCreate(SQLModel):
    """Friend link create body."""

    name: str
    url: str
    avatar_url: str | None = None
    description: str | None = None
    sort: int = 0


class FriendUpdate(SQLModel):
    """Friend link partial update body."""

    name: str | None = None
    url: str | None = None
    avatar_url: str | None = None
    description: str | None = None
    sort: int | None = None


class FriendOut(SQLModel):
    """Friend link response body."""

    id: int
    name: str
    url: str
    avatar_url: str | None = None
    description: str | None = None
    sort: int = 0


class ContributionDay(SQLModel):
    """One day in the GitHub contribution heatmap."""

    date: str
    count: int = 0
    level: int = 0


class GitHubContributions(SQLModel):
    """GitHub contribution summary."""

    total_last_year: int = 0
    days: list[ContributionDay] = Field(default_factory=list)


class GitHubCacheOut(SQLModel):
    """Cached GitHub profile payload."""

    login: str = ""
    name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    html_url: str | None = None
    readme_html: str = ""
    contributions: GitHubContributions = Field(default_factory=GitHubContributions)
    fetched_ts: int = 0


class GithubTokenIn(SQLModel):
    """GitHub PAT push body from the client."""

    token: str = Field(min_length=1, max_length=512)
    login: str | None = Field(default=None, max_length=100)


class GithubTokenOut(SQLModel):
    """GitHub PAT push ack payload."""

    configured: bool = True
    login: str = ""
    updated_ts: int = 0


class SiteOut(SQLModel):
    """Site copy payload."""

    title: str = "HeartBeat"
    tagline: str = ""
    process_title: str = ""
    show_heatmap: bool = True
    tags_title: str = "标签"
    tags: list[str] = Field(default_factory=list)
    show_icp: bool = False
    icp_text: str = ""
    icp_keyword: str = ""


class SiteUpdate(SQLModel):
    """Site copy partial update body."""

    title: str | None = Field(default=None, min_length=1, max_length=80)
    tagline: str | None = Field(default=None, max_length=200)
    process_title: str | None = Field(default=None, min_length=1, max_length=80)
    show_heatmap: bool | None = None
    tags_title: str | None = Field(default=None, min_length=1, max_length=80)
    tags: list[str] | None = None
    show_icp: bool | None = None
    icp_text: str | None = Field(default=None, max_length=80)
    icp_keyword: str | None = Field(default=None, max_length=64)

    @field_validator("title", "process_title", "tags_title")
    @classmethod
    def copy_must_not_be_blank(cls, value: str | None) -> str | None:
        """Reject blank site copy fields and trim their edges."""
        if value is None:
            return None
        text = value.strip()
        if not text:
            raise ValueError("must not be empty")
        return text

    @field_validator("tagline")
    @classmethod
    def tagline_trimmed(cls, value: str | None) -> str | None:
        """Trim tagline edges, allowing an empty result."""
        return None if value is None else value.strip()

    @field_validator("tags")
    @classmethod
    def tags_normalized(cls, value: list[str] | None) -> list[str] | None:
        """Trim tag texts and drop empties."""
        if value is None:
            return None
        cleaned = [item.strip() for item in value]
        return [item for item in cleaned if item][:32]



