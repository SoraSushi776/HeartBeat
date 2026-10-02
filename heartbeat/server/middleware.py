"""Request level guards applied before routing."""
from __future__ import annotations

import logging

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from heartbeat.server.envelope import error_body
from heartbeat.server.services.static_access import StaticAccessPolicy

logger = logging.getLogger(__name__)


class StaticGuardMiddleware(BaseHTTPMiddleware):
    """Reject static requests that fall outside the public asset policy."""

    def __init__(self, app: ASGIApp, policy: StaticAccessPolicy) -> None:
        """Store the policy used to vet static request paths."""
        super().__init__(app)
        self._policy = policy

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Answer 404 for static paths the policy does not allow."""
        path = request.url.path
        if self._policy.applies(path) and not self._policy.allows(path):
            logger.warning("Static asset blocked: path=%s", path)
            return JSONResponse(status_code=404, content=error_body(404, "Not Found"))
        return await call_next(request)
