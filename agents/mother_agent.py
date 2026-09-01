from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from ai.base_agent import Agent


class MotherAgent(Agent):
    """Executive coordinator with explicit, auditable decision boundaries.

    Mother does not execute business work itself. It creates prioritized commands
    for the supervisor/workflow layer. High-impact operations can require an
    approval flag before they are dispatched.
    """

    name = "mother"
    description = "Executive coordinator and final decision layer."

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.running = False
        self._queue: asyncio.PriorityQueue[tuple[int, int, dict[str, Any]]] = asyncio.PriorityQueue()
        self._sequence = 0
        self.decisions: list[dict[str, Any]] = []
        self.max_history = int(config.get("max_history", 100))
        self.require_approval_for = set(config.get("require_approval_for", ["live_trading", "deployment", "code_change"]))
        self.last_decision_at: str | None = None

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    def decide(self, objective: str, target_agents: list[str], priority: int = 50, action: str = "plan", approval_required: bool | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        if not objective.strip():
            raise ValueError("objective is required")
        if priority < 0 or priority > 100:
            raise ValueError("priority must be between 0 and 100")
        approval = bool(approval_required) if approval_required is not None else action in self.require_approval_for
        decision = {
            "id": f"decision-{self._sequence + 1}",
            "objective": objective.strip(),
            "target_agents": list(dict.fromkeys(target_agents)),
            "priority": priority,
            "action": action,
            "approval_required": approval,
            "approved": not approval,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "context": context or {},
        }
        self._sequence += 1
        self.decisions.append(decision)
        self.decisions = self.decisions[-self.max_history :]
        self.last_decision_at = decision["created_at"]
        return decision

    async def enqueue(self, decision: dict[str, Any]) -> None:
        if decision.get("approval_required") and not decision.get("approved"):
            raise PermissionError("Decision requires explicit approval before dispatch")
        await self._queue.put((100 - int(decision.get("priority", 50)), self._sequence, decision))

    def approve(self, decision_id: str) -> dict[str, Any]:
        for decision in reversed(self.decisions):
            if decision["id"] == decision_id:
                decision["approved"] = True
                decision["approved_at"] = datetime.now(timezone.utc).isoformat()
                return decision
        raise KeyError(decision_id)

    async def on_tick(self) -> None:
        # The executive layer remains deliberately side-effect free here. A
        # workflow/event adapter can consume approved decisions later.
        return None

    async def status(self) -> dict[str, Any]:
        return {
            "key": "mother",
            "name": self.name,
            "layer": "Executive",
            "running": self.running,
            "healthy": True,
            "role": "CEO / system brain",
            "decision_count": len(self.decisions),
            "queued_commands": self._queue.qsize(),
            "last_decision_at": self.last_decision_at,
            "approval_policy": sorted(self.require_approval_for),
            "external_side_effects": False,
        }
