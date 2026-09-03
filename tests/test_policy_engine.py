from policy.engine import CapabilityLevel, PolicyEngine


def test_policy_blocks_unknown_capability() -> None:
    engine = PolicyEngine()
    assert engine.get("unknown.action") is None
    assert engine.allows("unknown.action", CapabilityLevel.OBSERVE) is False


def test_policy_requires_approval_for_consequential_capabilities() -> None:
    engine = PolicyEngine()
    assert engine.get("trade.execute").level == CapabilityLevel.EXECUTE_WITH_APPROVAL
    assert engine.get("content.publish").level == CapabilityLevel.EXECUTE_WITH_APPROVAL
    assert engine.allows("content.publish", CapabilityLevel.DRAFT) is True
