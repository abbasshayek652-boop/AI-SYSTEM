from __future__ import annotations

import datetime as dt
from typing import Any

from sqlmodel import Session, select

from db.models import Approval
from db.session import engine
from policy.engine import CapabilityLevel, policy_engine
from services.event_store import record_event


def request_approval(
    *,
    capability: str,
    target: str,
    requested_by: str,
    payload: dict[str, Any] | None = None,
    reason: str | None = None,
    correlation_id: str | None = None,
) -> Approval:
    policy = policy_engine.get(capability)
    if policy is None or policy.level != CapabilityLevel.EXECUTE_WITH_APPROVAL:
        raise ValueError(f"Capability does not require approval or is not permitted: {capability}")
    approval = Approval(
        capability=capability,
        target=target,
        requested_by=requested_by,
        payload=payload or {},
        reason=reason,
        correlation_id=correlation_id,
    )
    with Session(engine) as session:
        session.add(approval)
        session.commit()
        session.refresh(approval)
        snapshot = approval.model_dump()
    record_event("approval.requested", payload={"approval": snapshot})
    return approval


def list_pending(limit: int = 100) -> list[Approval]:
    with Session(engine) as session:
        statement = select(Approval).where(Approval.status == "pending").order_by(Approval.created_ts.desc()).limit(max(1, min(limit, 200)))
        return list(session.exec(statement).all())


def decide(approval_id: int, *, approved: bool, decided_by: str, note: str | None = None) -> Approval:
    with Session(engine) as session:
        approval = session.get(Approval, approval_id)
        if approval is None:
            raise LookupError("Approval not found")
        if approval.status != "pending":
            raise ValueError("Approval is already decided")
        approval.status = "approved" if approved else "rejected"
        approval.decided_by = decided_by
        approval.decision_note = note
        approval.updated_ts = dt.datetime.utcnow()
        session.add(approval)
        session.commit()
        session.refresh(approval)
        snapshot = approval.model_dump()
    record_event("approval.decided", payload={"approval": snapshot})
    return approval
