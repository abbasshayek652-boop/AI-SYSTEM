from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from gateway.auth import AuthContext, get_viewer
from services.connections import connection_statuses
from services.event_store import recent_events

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/connections")
async def connections(request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    agents = getattr(request.app.state, "agents", {}) or {}
    items = connection_statuses(agents)
    return {
        "count": len(items),
        "configured_count": sum(item["configured"] for item in items),
        "items": items,
    }


@router.get("/events")
async def events(
    limit: int = 100,
    event_type: str | None = None,
    agent_key: str | None = None,
    _: AuthContext = Depends(get_viewer),
) -> dict[str, Any]:
    items = recent_events(limit=limit, event_type=event_type, agent_key=agent_key)
    return {
        "count": len(items),
        "events": [
            {
                "id": item.id,
                "ts": item.ts.isoformat() if item.ts else None,
                "agent_key": item.agent_key,
                "event_type": item.event_type,
                "payload": item.payload or {},
            }
            for item in items
        ],
    }
