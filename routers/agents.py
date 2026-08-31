from __future__ import annotations

import pathlib
from collections import deque
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import ValidationError

from ai.registry import Registry, hydrate_agents
from ai.base_agent import Agent
from gateway.auth import AuthContext, get_admin, get_viewer
from routers.core import _safe_agent_status


router = APIRouter()


def _log_path(agent_key: str) -> pathlib.Path:
    return pathlib.Path("logs") / f"{agent_key}.log"


def _read_logs(agent_key: str, limit: int = 2000) -> str:
    path = _log_path(agent_key)
    if not path.exists():
        return ""
    lines: deque[str] = deque(maxlen=limit)
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            lines.append(line.rstrip())
    return "\n".join(lines)


def _registry_entry(request: Request, key: str) -> dict[str, Any] | None:
    registry = getattr(request.app.state, "registry", None)
    for entry in getattr(registry, "agents", []) if registry else []:
        if getattr(entry, "key", None) == key:
            config = dict(getattr(entry, "config", {}) or {})
            # Never expose credentials or secret material through the dashboard API.
            secret_keys = {"api_key", "api_secret", "secret", "token", "password", "fernet_key", "webhook_url"}
            safe_config = {k: v for k, v in config.items() if k.lower() not in secret_keys}
            return {
                "enabled": bool(getattr(entry, "enabled", True)),
                "module": getattr(entry, "module", None),
                "class_name": getattr(entry, "class_name", None),
                "config": safe_config,
            }
    return None


@router.get("/agents")
async def list_agents(request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    """Return a frontend-friendly, stable representation of every loaded agent."""
    agents: dict[str, Agent] = getattr(request.app.state, "agents", {}) or {}
    results = await __import__("asyncio").gather(
        *(_safe_agent_status(key, agent) for key, agent in agents.items())
    )
    items: list[dict[str, Any]] = []
    for key, runtime in results:
        item = dict(runtime)
        item["registry"] = _registry_entry(request, key)
        items.append(item)
    return {
        "count": len(items),
        "running_count": sum(bool(item.get("running")) for item in items),
        "healthy_count": sum(bool(item.get("healthy")) for item in items),
        "agents": items,
    }


@router.get("/agents/{agent_key}")
async def get_agent(agent_key: str, request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    agents: dict[str, Agent] = getattr(request.app.state, "agents", {}) or {}
    agent = agents.get(agent_key)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent")
    _, payload = await _safe_agent_status(agent_key, agent)
    payload["registry"] = _registry_entry(request, agent_key)
    return payload


@router.get("/logs/{agent_key}")
async def agent_logs(agent_key: str, request: Request, _: AuthContext = Depends(get_viewer)) -> Response:
    agents = getattr(request.app.state, "agents", None) or {}
    if agent_key not in agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent")
    content = _read_logs(agent_key)
    return Response(content=content, media_type="text/plain")


@router.post("/registry/validate")
async def registry_validate(request: Request, _: AuthContext = Depends(get_admin)) -> dict[str, Any]:
    payload = await request.json()
    try:
        Registry(**payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/registry/dryrun")
async def registry_dryrun(request: Request, _: AuthContext = Depends(get_admin)) -> dict[str, Any]:
    payload = await request.json()
    registry = Registry(**payload)
    instances = hydrate_agents(registry)
    summary = {key: instance.__class__.__name__ for key, instance in instances.items()}
    return {"ok": True, "agents": summary}
