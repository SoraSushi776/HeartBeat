"""Response envelope helpers matching the JSON protocol."""
from __future__ import annotations

from typing import Any

ERROR_CODES: dict[int, str] = {
    400: "invalid_payload",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    429: "rate_limited",
}


def ok(data: Any) -> dict[str, Any]:
    """Return a success envelope with the given data."""
    return {"ok": True, "data": data}


def error_body(status_code: int, message: str) -> dict[str, Any]:
    """Return a protocol error envelope for the given status code."""
    code = ERROR_CODES.get(status_code, "error")
    return {"ok": False, "error": {"code": code, "message": message}}


class ApiError(Exception):
    """Protocol-shaped HTTP error raised by route handlers."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
