"""UTC millisecond clock helpers."""
from __future__ import annotations

import time


def current_ms() -> int:
    """Return the current UTC timestamp in milliseconds."""
    return int(time.time() * 1000)
