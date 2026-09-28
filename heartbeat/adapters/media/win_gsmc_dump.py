"""Print GSMTC media sessions for local diagnostics."""

from __future__ import annotations

import asyncio
import json
from typing import Any


async def dump() -> dict[str, Any]:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager,
    )

    manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
    current = manager.get_current_session()
    sessions = list(manager.get_sessions() or [])
    rows = []
    for index, session in enumerate([current, *sessions]):
        if session is None:
            continue
        item: dict[str, Any] = {
            "index": index,
            "app": getattr(session, "source_app_user_model_id", ""),
        }
        try:
            props = await session.try_get_media_properties_async()
            item["title"] = getattr(props, "title", "")
            item["artist"] = getattr(props, "artist", "")
            item["album"] = getattr(props, "album_title", "")
        except Exception as exc:
            item["props_error"] = str(exc)
        try:
            info = session.get_playback_info()
            status = getattr(info, "playback_status", None)
            item["status"] = getattr(status, "name", str(status))
        except Exception as exc:
            item["status_error"] = str(exc)
        try:
            timeline = session.get_timeline_properties()
            item["position_s"] = str(getattr(timeline, "position", ""))
            item["end_s"] = str(getattr(timeline, "end_time", ""))
        except Exception as exc:
            item["timeline_error"] = str(exc)
        rows.append(item)
    return {"current": getattr(current, "source_app_user_model_id", None), "sessions": rows}


def main() -> None:
    try:
        payload = asyncio.run(dump())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
