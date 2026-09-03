from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from gateway.auth import AuthContext, get_operator
from services.approvals import get_approval, request_approval
from .models import PostRequest, ScheduleRequest
from .service import service
from .scheduler import start_scheduler

router = APIRouter()


def _parse_datetime(value: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid datetime format") from exc


@router.get("/agents/linkedin/login")
def login() -> RedirectResponse:
    return RedirectResponse(service.login_url())


@router.get("/agents/linkedin/callback")
def callback(code: str, state: str | None = None) -> Dict[str, Any]:
    return service.handle_callback(code, state)


@router.post("/agents/linkedin/post/text")
def request_text_approval(payload: Dict[str, Any], ctx: AuthContext = Depends(get_operator)) -> Dict[str, Any]:
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    visibility = str(payload.get("visibility", "PUBLIC"))
    approval = request_approval(
        capability="content.publish",
        target="linkedin",
        requested_by=ctx.user_id,
        payload={"text": str(text), "visibility": visibility},
        reason="LinkedIn post requested through Mother AI",
    )
    return {"ok": True, "approval_id": approval.id, "status": approval.status}


@router.post("/agents/linkedin/approvals/{approval_id}/publish")
def publish_approved(approval_id: int, ctx: AuthContext = Depends(get_operator)) -> Dict[str, Any]:
    approval = get_approval(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "approved":
        raise HTTPException(status_code=409, detail="Approval is not approved")
    if approval.capability != "content.publish" or approval.target != "linkedin":
        raise HTTPException(status_code=400, detail="Approval is not a LinkedIn publish approval")
    payload = approval.payload or {}
    result = service.post_text(str(payload.get("text", "")), str(payload.get("visibility", "PUBLIC")))
    return {"ok": True, "approval_id": approval_id, "published_by": ctx.user_id, "result": result}


@router.post("/agents/linkedin/post/document")
def request_document_approval(payload: Dict[str, Any], ctx: AuthContext = Depends(get_operator)) -> Dict[str, Any]:
    model = PostRequest(**payload)
    if not model.doc_path:
        raise HTTPException(status_code=400, detail="doc_path required")
    approval = request_approval(
        capability="content.publish",
        target="linkedin",
        requested_by=ctx.user_id,
        payload=model.model_dump(mode="json"),
        reason="LinkedIn document post requested through Mother AI",
    )
    return {"ok": True, "approval_id": approval.id, "status": approval.status}


@router.post("/agents/linkedin/schedule")
def schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "run_at" in payload and isinstance(payload["run_at"], str):
        payload["run_at"] = _parse_datetime(payload["run_at"])
    request = ScheduleRequest(**payload)
    return {"scheduled_id": service.schedule_post(request)}


@router.get("/agents/linkedin/schedule")
def list_schedule() -> Dict[str, Any]:
    return {"items": service.list_scheduled()}


@router.get("/agents/linkedin/health")
def health() -> Dict[str, Any]:
    return service.health()


__all__ = ["router", "start_scheduler"]
