"""Site title, tagline and process block copy routes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.config import load_site_settings, save_site_settings
from heartbeat.server.dependencies import require_api_key
from heartbeat.server.envelope import ok
from heartbeat.server.schemas import SiteOut, SiteUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_PREFIX}/site", tags=["site"])

write_deps = [Depends(require_api_key)]


@router.get("")
def get_site() -> dict[str, Any]:
    """Return the site title, tagline and process block copy."""
    return ok(SiteOut(**load_site_settings()).model_dump(mode="json"))


@router.put("", dependencies=write_deps)
def update_site(payload: SiteUpdate) -> dict[str, Any]:
    """Merge the provided site copy fields into the stored settings."""
    values = {
        key: value
        for key, value in payload.model_dump(exclude_unset=True).items()
        if value is not None
    }
    stored = save_site_settings(values) if values else load_site_settings()
    logger.info("Site settings updated: fields=%s", sorted(values))
    return ok(SiteOut(**stored).model_dump(mode="json"))
