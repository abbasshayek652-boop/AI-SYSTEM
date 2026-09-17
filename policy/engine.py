from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CapabilityLevel(StrEnum):
    OBSERVE = "observe"
    ANALYZE = "analyze"
    RECOMMEND = "recommend"
    DRAFT = "draft"
    EXECUTE_WITH_APPROVAL = "execute_with_approval"
    EXECUTE_AUTOMATICALLY = "execute_automatically"


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    capability: str
    level: CapabilityLevel
    enabled: bool = True


DEFAULT_POLICIES: tuple[CapabilityPolicy, ...] = (
    CapabilityPolicy("account.read", CapabilityLevel.OBSERVE),
    CapabilityPolicy("market.read", CapabilityLevel.OBSERVE),
    CapabilityPolicy("balances.read", CapabilityLevel.OBSERVE),
    CapabilityPolicy("content.draft", CapabilityLevel.DRAFT),
    CapabilityPolicy("content.publish", CapabilityLevel.EXECUTE_WITH_APPROVAL),
    CapabilityPolicy("message.send", CapabilityLevel.EXECUTE_WITH_APPROVAL),
    CapabilityPolicy("trade.execute", CapabilityLevel.EXECUTE_WITH_APPROVAL),
)


class PolicyEngine:
    def __init__(self, policies: tuple[CapabilityPolicy, ...] = DEFAULT_POLICIES) -> None:
        self._policies = {item.capability: item for item in policies}

    def get(self, capability: str) -> CapabilityPolicy | None:
        return self._policies.get(capability)

    def allows(self, capability: str, requested: CapabilityLevel) -> bool:
        policy = self.get(capability)
        if policy is None or not policy.enabled:
            return False
        order = list(CapabilityLevel)
        return order.index(policy.level) >= order.index(requested)

    def public_policies(self) -> list[dict[str, object]]:
        return [
            {"capability": item.capability, "level": item.level.value, "enabled": item.enabled}
            for item in self._policies.values()
        ]


policy_engine = PolicyEngine()
