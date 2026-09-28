"""Build the HeartBeat desktop client with pyside6-deploy."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "heartbeat" / "client" / "main.py"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd or ROOT)


def ensure_icons() -> None:
    run([sys.executable, str(ROOT / "scripts" / "generate_icons.py")])


def ensure_deploy() -> str:
    candidate = shutil.which("pyside6-deploy")
    if candidate:
        return candidate
    run([sys.executable, "-m", "pip", "install", "pyside6-deploy", "nuitka", "ordered-set", "zstandard"])
    return shutil.which("pyside6-deploy") or ""


def main() -> None:
    ensure_icons()
    deploy = ensure_deploy()
    if not deploy:
        print("pyside6-deploy not found on PATH", file=sys.stderr)
        raise SystemExit(1)
    os.chdir(ROOT)
    run([deploy, str(ENTRY)])
    print("Build finished. Artifacts are near the project root / pyside6-deploy output folder.")


if __name__ == "__main__":
    main()
