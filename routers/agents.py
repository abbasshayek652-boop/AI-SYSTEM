from __future__ import annotations

import asyncio
import pathlib
from collections import deque
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, ValidationError

from ai.base_agent import Agent
from ai.registry import Registry, hydrate_agents
from gateway.auth import AuthContext, get_admin, get_operator, get_viewer
from routers.core import _safe_agent_status

router = APIRouter()


SECRET_CONFIG_KEYS = {"api_key", "api_secret", "secret", "token", "password", "fernet_key", "webhook_url"}


class AgentExecuteRequest(BaseModel):
    action: str = Field(default="inspect", min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)


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
        if getattr(entry, "key", None) != key:
            continue
        config = dict(getattr(entry, "config", {}) or {})
        safe_config = {k: v for k, v in config.items() if k.lower() not in SECRET_CONFIG_KEYS}
        return {"enabled": bool(getattr(entry, "enabled", True)), "module": getattr(entry, "module", None), "class_name": getattr(entry, "class_name", None), "config": safe_config}
    return None


async def _agent_items(request: Request) -> list[dict[str, Any]]:
    agents: dict[str, Agent] = getattr(request.app.state, "agents", {}) or {}
    results = await asyncio.gather(*(_safe_agent_status(key, agent) for key, agent in agents.items()))
    items: list[dict[str, Any]] = []
    for key, runtime in results:
        item = dict(runtime)
        item["registry"] = _registry_entry(request, key)
        items.append(item)
    return items


@router.get("/agents")
async def list_agents(request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    items = await _agent_items(request)
    return {"count": len(items), "running_count": sum(bool(item.get("running")) for item in items), "healthy_count": sum(bool(item.get("healthy")) for item in items), "agents": items}


@router.get("/agents/{agent_key}")
async def get_agent(agent_key: str, request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    agents: dict[str, Agent] = getattr(request.app.state, "agents", {}) or {}
    agent = agents.get(agent_key)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent")
    _, payload = await _safe_agent_status(agent_key, agent)
    payload["registry"] = _registry_entry(request, agent_key)
    return payload


@router.post("/agents/{agent_key}/execute")
async def execute_agent(agent_key: str, request: Request, payload: AgentExecuteRequest, _: AuthContext = Depends(get_operator)) -> dict[str, Any]:
    """Run a local agent capability through its safe execute interface."""
    agents: dict[str, Agent] = getattr(request.app.state, "agents", {}) or {}
    agent = agents.get(agent_key)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent")
    execute = getattr(agent, "execute", None)
    if not callable(execute):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent does not expose an execute interface")
    try:
        result = await execute(payload.action, payload.payload)
    except TypeError:
        try:
            result = await execute(**payload.payload)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc
    return {"ok": True, "agent": agent_key, "action": payload.action, "result": result}


@router.get("/logs/{agent_key}")
async def agent_logs(agent_key: str, request: Request, _: AuthContext = Depends(get_viewer)) -> Response:
    agents = getattr(request.app.state, "agents", None) or {}
    if agent_key not in agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent")
    return Response(content=_read_logs(agent_key), media_type="text/plain")


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
