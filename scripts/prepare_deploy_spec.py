"""Keep pysidedeploy.spec non-interactive so packaging can run unattended."""

from __future__ import annotations

import logging
import re
import shlex
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

NUITKA_FLAGS = ("--assume-yes-for-downloads",)
EXTRA_ARGS_LINE = re.compile(r"^(\s*extra_args\s*=\s*)(.*)$", re.MULTILINE)


def spec_path(entry: Path) -> Path:
    """Return the deployment spec path that pyside6-deploy uses for the entry file."""
    return entry.parent / "pysidedeploy.spec"


def create_spec(deploy: str, entry: Path) -> None:
    """Ask pyside6-deploy to write a fresh spec next to the entry file."""
    subprocess.run([deploy, "--init", str(entry)], check=True)


def merge_flags(spec: Path) -> bool:
    """Append the non-interactive Nuitka flags, returning whether the spec changed."""
    text = spec.read_text(encoding="utf-8")
    match = EXTRA_ARGS_LINE.search(text)
    if match is None:
        logger.warning("No extra_args line in %s", spec)
        return False
    flags = shlex.split(match.group(2))
    missing = [flag for flag in NUITKA_FLAGS if flag not in flags]
    if not missing:
        return False
    merged = " ".join([*flags, *missing])
    spec.write_text(f"{text[:match.start(2)]}{merged}{text[match.end(2):]}", encoding="utf-8")
    logger.info("Added Nuitka flags to %s: %s", spec, " ".join(missing))
    return True


def prepare(deploy: str, entry: Path) -> Path:
    """Make sure a non-interactive spec exists for the entry file."""
    spec = spec_path(entry)
    if not spec.exists():
        logger.info("Creating deployment spec: %s", spec)
        create_spec(deploy, entry)
    merge_flags(spec)
    return spec


def main() -> None:
    """Prepare the deployment spec for the given deploy command and entry file."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) < 3:
        logger.error("usage: prepare_deploy_spec.py <pyside6-deploy> <entry.py>")
        raise SystemExit(2)
    spec = prepare(sys.argv[1], Path(sys.argv[2]).resolve())
    logger.info("Deployment spec ready: %s", spec)


if __name__ == "__main__":
    main()
