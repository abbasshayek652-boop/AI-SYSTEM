from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from db.models import Approval
from policy.engine import CapabilityLevel, PolicyEngine


def test_approval_model_defaults_to_pending() -> None:
    item = Approval(capability="content.publish", target="linkedin", requested_by="operator")
    assert item.status == "pending"


def test_policy_levels_are_ordered_for_safe_actions() -> None:
    engine = PolicyEngine()
    assert engine.allows("content.publish", CapabilityLevel.DRAFT)
    assert not engine.allows("content.publish", CapabilityLevel.EXECUTE_AUTOMATICALLY)
