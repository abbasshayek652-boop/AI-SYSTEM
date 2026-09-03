from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from gateway.auth import AuthContext, get_viewer
from integrations.bootstrap import register_default_adapters
from integrations.registry import health_all

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/health")
async def health(_: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    register_default_adapters()
    items = [item.public_dict() for item in health_all()]
    return {"count": len(items), "healthy_count": sum(bool(item["healthy"]) for item in items), "items": items}
