from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from ai.base_agent import Agent
from db.models import AgentEvent
from db.session import engine
from gateway.auth import AuthContext, get_viewer
from gateway.guards import circuit_breaker


router = APIRouter()


async def _safe_agent_status(key: str, agent: Agent) -> tuple[str, dict[str, Any]]:
    """Return an isolated status result so one unhealthy agent cannot break /status."""
    try:
        payload = await agent.status()
        if not isinstance(payload, dict):
            payload = {"value": payload}
        return key, {
            **payload,
            "key": key,
            "name": getattr(agent, "name", key),
            "description": getattr(agent, "description", ""),
            "class_name": agent.__class__.__name__,
            "running": bool(getattr(agent, "running", False)),
            "healthy": True,
            "status_error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return key, {
            "key": key,
            "name": getattr(agent, "name", key),
            "description": getattr(agent, "description", ""),
            "class_name": agent.__class__.__name__,
            "running": bool(getattr(agent, "running", False)),
            "healthy": False,
            "status_error": str(exc),
        }


async def status_payload(app) -> dict[str, Any]:
    agents: dict[str, Agent] = getattr(app.state, "agents", {}) or {}
    keys = list(agents.keys())
    results = await asyncio.gather(*(_safe_agent_status(key, agents[key]) for key in keys))
    agent_payload = {key: payload for key, payload in results}
    running = {key: bool(agent_payload[key].get("running", False)) for key in keys}
    healthy = {key: bool(agent_payload[key].get("healthy", False)) for key in keys}
    return {
        "loaded_agents": keys,
        "agent_count": len(keys),
        "running_count": sum(running.values()),
        "healthy_count": sum(healthy.values()),
        "running": running,
        "agents": agent_payload,
        "circuit_breaker": circuit_breaker.state(),
        "last_audit_ts": getattr(app.state, "last_audit_ts", None),
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def _db_ready() -> bool:
    try:
        with Session(engine) as session:
            session.exec(select(AgentEvent).limit(1)).all()
        return True
    except Exception:  # noqa: BLE001
        return False


@router.get("/healthz")
async def healthz() -> dict[str, object]:
    return {
        "ok": True,
        "status": "ok",
        "service": "mother_ai",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


@router.get("/readyz")
async def readyz(request: Request) -> dict[str, object]:
    db_ok = _db_ready()
    registry_ok = getattr(request.app.state, "registry", None) is not None
    agents_ok = isinstance(getattr(request.app.state, "agents", None), dict)
    app_ready = bool(getattr(request.app.state, "ready", False))
    ready = all([db_ok, registry_ok, agents_ok, app_ready])
    return {
        "ready": ready,
        "db": db_ok,
        "registry": registry_ok,
        "agents": agents_ok,
        "agent_count": len(getattr(request.app.state, "agents", {}) or {}),
    }


@router.get("/status")
async def status_endpoint(request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    return await status_payload(request.app)
