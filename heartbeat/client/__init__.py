from __future__ import annotations

__all__ = ["launch_command", "run"]


def run() -> None:
    from heartbeat.client.main import run as _run

    _run()


def launch_command() -> str:
    from heartbeat.client.main import launch_command as _launch_command

    return _launch_command()
