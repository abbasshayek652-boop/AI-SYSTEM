from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from ai.agent_catalog import CATALOG_VERSION, catalog, catalog_layers, get_catalog_entry
from gateway.auth import AuthContext, get_viewer

router = APIRouter()


@router.get("/catalog")
async def agent_catalog(request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    """Return the complete product catalog plus current runtime state."""
    runtime = getattr(request.app.state, "agents", {}) or {}
    items = []
    for item in catalog():
        agent = runtime.get(item["key"])
        runtime_status: dict[str, Any] = {
            "loaded": agent is not None,
            "running": False,
            "healthy": False,
        }
        if agent is not None:
            try:
                payload = await agent.status()
                runtime_status.update({
                    "running": bool(getattr(agent, "running", False)),
                    "healthy": bool(payload.get("healthy", True)),
                })
            except Exception as exc:
                runtime_status["error"] = str(exc)
        items.append({**item, "runtime": runtime_status})
    return {
        "catalog_version": CATALOG_VERSION,
        "count": len(items),
        "loaded_count": sum(x["runtime"]["loaded"] for x in items),
        "running_count": sum(x["runtime"]["running"] for x in items),
        "layers": catalog_layers(),
        "agents": items,
    }


@router.get("/catalog/{agent_key}")
async def catalog_agent(agent_key: str, request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    item = get_catalog_entry(agent_key)
    if item is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unknown catalog agent")
    runtime = getattr(request.app.state, "agents", {}) or {}
    agent = runtime.get(agent_key)
    result = dict(item)
    result["runtime"] = {"loaded": agent is not None, "running": bool(getattr(agent, "running", False)) if agent else False}
    return result
