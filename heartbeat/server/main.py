"""FastAPI application assembly and server entrypoint."""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from heartbeat.logging_util import setup_logging
from heartbeat.server.config import get_settings
from heartbeat.server.db import init_db
from heartbeat.server.envelope import ApiError, error_body
from heartbeat.server.routers import diaries, friends, github, heartbeat, screenshot, status
from heartbeat.server.services.scheduler import create_scheduler

logger = logging.getLogger(__name__)

DESCRIPTION = "HeartBeat FastAPI server"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize database, static dirs and background scheduler."""
    settings = get_settings()
    init_db()
    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Server started on data_dir=%s", settings.data_dir)
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Server shutdown complete")


def create_app() -> FastAPI:
    """Build the FastAPI application with routes, middleware and handlers."""
    settings = get_settings()
    app = FastAPI(title=DESCRIPTION, lifespan=lifespan)
    _register_exception_handlers(app)
    _register_cors(app, settings.cors_origins)
    app.include_router(heartbeat.router)
    app.include_router(screenshot.router)
    app.include_router(status.router)
    app.include_router(diaries.router)
    app.include_router(friends.router)
    app.include_router(github.router)
    app.mount("/static", StaticFiles(directory=str(settings.data_dir)), name="static")
    _register_frontend(app)
    return app


def _register_frontend(app: FastAPI) -> None:
    """Serve the built Dashboard when frontend/dist is available."""
    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if not dist.is_dir():
        logger.warning("Frontend dist missing: %s", dist)
        return
    app.frontend("/", directory=str(dist))


def _register_cors(app: FastAPI, origins: list[str]) -> None:
    """Attach CORS middleware when origins are configured."""
    if not origins:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_exception_handlers(app: FastAPI) -> None:
    """Map internal exceptions onto the protocol error envelope."""

    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        """Render ApiError using the protocol error envelope."""
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.status_code, exc.message),
        )

    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Render Starlette HTTPException using the protocol error envelope."""
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.status_code, message),
        )

    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Render request validation failures as invalid_payload errors."""
        parts = [f"{list(err.get('loc', []))}: {err.get('msg', 'invalid')}" for err in exc.errors()]
        return JSONResponse(status_code=400, content=error_body(400, "; ".join(parts)))

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)


app = create_app()


def run() -> None:
    """Start the uvicorn server using the current settings."""
    setup_logging()
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    run()
