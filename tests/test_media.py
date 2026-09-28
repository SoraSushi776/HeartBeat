"""媒体解析测试"""

from heartbeat.adapters.media.linux import parse_metadata
from heartbeat.adapters.media.macos import parse_script_output
from heartbeat.protocol.models import MediaState


def test_parse_script_output_idle() -> None:
    assert parse_script_output("", "Music").state is MediaState.IDLE
    assert parse_script_output("idle", "Music").state is MediaState.IDLE


def test_parse_script_output_playing() -> None:
    raw = "playing\x1fSong\x1fArtist\x1fAlbum\x1f210000\x1f42500"
    info = parse_script_output(raw, "Music")
    assert info.state is MediaState.PLAYING
    assert info.title == "Song"
    assert info.artist == "Artist"
    assert info.album == "Album"
    assert info.app == "Music"
    assert info.duration_ms == 210000
    assert info.position_ms == 42500
    assert info.cover_url is None


def test_parse_script_output_spotify_cover() -> None:
    raw = "paused\x1fSong\x1fArtist\x1fAlbum\x1f1000\x1f500\x1fhttps://cdn/cover.jpg"
    info = parse_script_output(raw, "Spotify")
    assert info.state is MediaState.PAUSED
    assert info.cover_url == "https://cdn/cover.jpg"


def test_parse_metadata_mpris() -> None:
    metadata = {
        "xesam:title": "Song",
        "xesam:artist": ["Artist A", "Artist B"],
        "xesam:album": "Album",
        "mpris:artUrl": "file:///tmp/cover.png",
        "mpris:length": 210_000_000,
    }
    info = parse_metadata(metadata, "Playing", "spotify")
    assert info.state is MediaState.PLAYING
    assert info.artist == "Artist A, Artist B"
    assert info.duration_ms == 210000
    assert info.cover_url == "file:///tmp/cover.png"
    assert info.app == "spotify"
