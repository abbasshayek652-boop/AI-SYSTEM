from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from gateway.auth import AuthContext, get_operator
from services.approvals import decide, list_pending, request_approval

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalRequest(BaseModel):
    capability: str
    target: str
    reason: str | None = None
    payload: dict[str, Any] = {}


class ApprovalDecision(BaseModel):
    approved: bool
    note: str | None = None


def _public(item: Any) -> dict[str, Any]:
    return item.model_dump(mode="json")


@router.get("")
async def pending(_: AuthContext = Depends(get_operator)) -> dict[str, Any]:
    items = list_pending()
    return {"count": len(items), "items": [_public(item) for item in items]}


@router.post("")
async def create(payload: ApprovalRequest, ctx: AuthContext = Depends(get_operator)) -> dict[str, Any]:
    try:
        item = request_approval(
            capability=payload.capability,
            target=payload.target,
            requested_by=ctx.user_id,
            reason=payload.reason,
            payload=payload.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True, "approval": _public(item)}


@router.post("/{approval_id}/decision")
async def decision(approval_id: int, payload: ApprovalDecision, ctx: AuthContext = Depends(get_operator)) -> dict[str, Any]:
    try:
        item = decide(approval_id, approved=payload.approved, decided_by=ctx.user_id, note=payload.note)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {"ok": True, "approval": _public(item)}
