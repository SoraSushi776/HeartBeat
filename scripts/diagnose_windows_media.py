"""Windows media capture diagnostic. Run with: python scripts/diagnose_windows_media.py"""

from __future__ import annotations

import asyncio
import json
import sys
import traceback


def banner(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def main() -> int:
    banner("1. Environment")
    print("python:", sys.version)
    print("executable:", sys.executable)
    print("platform:", sys.platform)

    banner("2. winrt import")
    try:
        import winrt.windows.media.control as media_control

        print("winrt.windows.media.control: OK")
        print("module file:", getattr(media_control, "__file__", "?"))
    except Exception:
        traceback.print_exc()
        print("RESULT: winrt not importable")
        return 1

    banner("3. GSMTC raw sessions")
    try:
        payload = asyncio.run(_dump_sessions())
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    except Exception:
        traceback.print_exc()
        print("RESULT: GSMTC query failed")
        return 1

    banner("4. WindowsMediaAdapter.collect")
    try:
        from heartbeat.adapters.privacy import PrivacyGate
        from heartbeat.adapters.media.windows import WindowsMediaAdapter

        adapter = WindowsMediaAdapter()
        info = adapter.collect(PrivacyGate())
        if info is None:
            print("RESULT: collect returned None (privacy blocked?)")
            return 1
        print(
            {
                "state": getattr(info.state, "value", info.state),
                "title": info.title,
                "artist": info.artist,
                "album": info.album,
                "app": info.app,
                "position_ms": info.position_ms,
                "duration_ms": info.duration_ms,
            }
        )
        if info.title or info.artist:
            print("RESULT: media captured OK")
        else:
            print("RESULT: adapter ran but no title/artist (check sessions above)")
    except Exception:
        traceback.print_exc()
        print("RESULT: adapter failed")
        return 1

    banner("Done")
    return 0


async def _dump_sessions() -> dict:
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager

    manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
    current = manager.get_current_session()
    sessions = list(manager.get_sessions() or [])
    rows = []
    for index, session in enumerate(sessions):
        row = {"kind": "sessions[%d]" % index}
        row.update(await _read_session(session))
        rows.append(row)
    current_row = {"kind": "current"}
    if current is not None:
        current_row.update(await _read_session(current))
    else:
        current_row["note"] = "get_current_session() returned None"
    return {"current": current_row, "count": len(sessions), "sessions": rows}


async def _read_session(session) -> dict:
    out: dict = {
        "app": getattr(session, "source_app_user_model_id", ""),
    }
    try:
        props = await session.try_get_media_properties_async()
        out["title"] = getattr(props, "title", "")
        out["artist"] = getattr(props, "artist", "")
        out["album"] = getattr(props, "album_title", "")
    except Exception as exc:
        out["props_error"] = repr(exc)
    try:
        info = session.get_playback_info()
        status = getattr(info, "playback_status", None)
        out["status"] = getattr(status, "name", str(status))
    except Exception as exc:
        out["status_error"] = repr(exc)
    try:
        timeline = session.get_timeline_properties()
        out["position_s"] = str(getattr(timeline, "position", ""))
        out["end_time_s"] = str(getattr(timeline, "end_time", ""))
    except Exception as exc:
        out["timeline_error"] = repr(exc)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
