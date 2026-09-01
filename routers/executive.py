from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from agents.mother_agent import MotherAgent
from gateway.auth import AuthContext, get_admin, get_operator, get_viewer

router = APIRouter(prefix="/executive", tags=["executive"])


class DecisionRequest(BaseModel):
    objective: str = Field(min_length=1, max_length=2000)
    target_agents: list[str] = Field(default_factory=list)
    priority: int = Field(default=50, ge=0, le=100)
    action: str = Field(default="plan", min_length=1, max_length=100)
    approval_required: bool | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    decision_id: str = Field(min_length=1, max_length=200)


def _mother(request: Request) -> MotherAgent:
    agent = (getattr(request.app.state, "agents", {}) or {}).get("mother")
    if not isinstance(agent, MotherAgent):
        raise HTTPException(status_code=503, detail="Mother Agent is not available")
    return agent


@router.get("/status")
async def executive_status(request: Request, _: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    mother = _mother(request)
    return await mother.status()


@router.post("/decide")
async def create_decision(request: Request, payload: DecisionRequest, _: AuthContext = Depends(get_operator)) -> dict[str, Any]:
    mother = _mother(request)
    unknown = [key for key in payload.target_agents if key not in (getattr(request.app.state, "agents", {}) or {})]
    if unknown:
        raise HTTPException(status_code=400, detail={"unknown_agents": unknown})
    return mother.decide(**payload.model_dump())


@router.post("/approve")
async def approve_decision(request: Request, payload: ApprovalRequest, _: AuthContext = Depends(get_admin)) -> dict[str, Any]:
    mother = _mother(request)
    try:
        return mother.approve(payload.decision_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown decision") from exc


@router.post("/dispatch/{decision_id}")
async def dispatch_decision(request: Request, decision_id: str, _: AuthContext = Depends(get_operator)) -> dict[str, Any]:
    mother = _mother(request)
    decision = next((item for item in reversed(mother.decisions) if item["id"] == decision_id), None)
    if decision is None:
        raise HTTPException(status_code=404, detail="Unknown decision")
    try:
        await mother.enqueue(decision)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"ok": True, "decision": decision, "queue_depth": mother._queue.qsize()}
