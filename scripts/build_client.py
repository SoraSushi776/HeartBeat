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
    """Return the pyside6-deploy executable, installing its Nuitka dependencies."""
    run([sys.executable, "-m", "pip", "install", "-q", "nuitka", "ordered-set", "zstandard"])
    beside = Path(sys.executable).with_name("pyside6-deploy")
    if beside.exists():
        return str(beside)
    return shutil.which("pyside6-deploy") or ""


def main() -> None:
    ensure_icons()
    deploy = ensure_deploy()
    if not deploy:
        print("pyside6-deploy not found. It ships inside PySide6, not on PyPI.", file=sys.stderr)
        raise SystemExit(1)
    if sys.prefix != sys.base_prefix:
        os.environ.setdefault("VIRTUAL_ENV", sys.prefix)
    os.chdir(ROOT)
    run([sys.executable, str(ROOT / "scripts" / "prepare_deploy_spec.py"), deploy, str(ENTRY)])
    run([deploy, "--force", str(ENTRY)])
    print("Build finished. Artifacts are near the project root / pyside6-deploy output folder.")


if __name__ == "__main__":
    main()
