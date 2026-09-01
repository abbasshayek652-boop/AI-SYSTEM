from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ai.agent_catalog import CATALOG_VERSION, catalog, catalog_layers, get_catalog_entry
from gateway.auth import AuthContext, get_viewer
from routers.core import _safe_agent_status

router = APIRouter()


@router.get("/catalog")
async def agent_catalog(request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    """Return the complete catalog with current runtime state.

    Status collection is concurrent and exception-isolated so one slow/broken
    agent cannot make the dashboard timeout or fail completely.
    """
    runtime = getattr(request.app.state, "agents", {}) or {}
    keys = list(runtime.keys())
    status_results = await asyncio.gather(
        *(_safe_agent_status(key, runtime[key]) for key in keys),
        return_exceptions=True,
    )
    runtime_by_key: dict[str, dict[str, Any]] = {}
    for key, result in zip(keys, status_results):
        if isinstance(result, Exception):
            runtime_by_key[key] = {"loaded": True, "running": False, "healthy": False, "error": str(result)}
            continue
        _, payload = result
        runtime_by_key[key] = {
            "loaded": True,
            "running": bool(payload.get("running", False)),
            "healthy": bool(payload.get("healthy", False)),
        }

    items = []
    for item in catalog():
        runtime_status = runtime_by_key.get(item["key"], {"loaded": False, "running": False, "healthy": False})
        items.append({**item, "runtime": runtime_status})

    return {
        "catalog_version": CATALOG_VERSION,
        "count": len(items),
        "loaded_count": sum(bool(x["runtime"]["loaded"]) for x in items),
        "running_count": sum(bool(x["runtime"]["running"]) for x in items),
        "layers": catalog_layers(),
        "agents": items,
    }


@router.get("/catalog/{agent_key}")
async def catalog_agent(agent_key: str, request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    item = get_catalog_entry(agent_key)
    if item is None:
        raise HTTPException(status_code=404, detail="Unknown catalog agent")
    runtime = getattr(request.app.state, "agents", {}) or {}
    agent = runtime.get(agent_key)
    result = dict(item)
    result["runtime"] = {"loaded": agent is not None, "running": bool(getattr(agent, "running", False)) if agent else False}
    return result
