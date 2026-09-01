from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from ai.base_agent import Agent


class SchedulerAgent(Agent):
    """Agent-facing scheduler facade. The gateway scheduler remains the runtime clock."""

    name = "scheduler"
    description = "Coordinates scheduled work without executing business logic."

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.running = False
        self.jobs: dict[str, dict[str, Any]] = {}

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    def register_job(self, job_id: str, schedule: str, target: str, priority: int = 50) -> dict[str, Any]:
        job = {"id": job_id, "schedule": schedule, "target": target, "priority": priority, "enabled": True}
        self.jobs[job_id] = job
        return job

    async def on_tick(self) -> None:
        return None

    async def status(self) -> dict[str, Any]:
        return {
            "key": self.name,
            "layer": "Executive",
            "running": self.running,
            "healthy": True,
            "job_count": len(self.jobs),
            "jobs": list(self.jobs.values()),
            "external_side_effects": False,
        }


class WorkflowAgent(Agent):
    """Safe workflow dispatcher facade. Actual integrations are adapters."""

    name = "workflow"
    description = "Executes approved workflow definitions through adapters."

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.running = False
        self.executions: list[dict[str, Any]] = []

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    async def execute(self, workflow_id: str, inputs: dict[str, Any] | None = None, approved: bool = False) -> dict[str, Any]:
        if not approved:
            raise PermissionError("Workflow execution requires approval")
        result = {
            "workflow_id": workflow_id,
            "inputs": inputs or {},
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.executions.append(result)
        self.executions = self.executions[-100:]
        return result

    async def on_tick(self) -> None:
        return None

    async def status(self) -> dict[str, Any]:
        return {
            "key": self.name,
            "layer": "Executive",
            "running": self.running,
            "healthy": True,
            "execution_count": len(self.executions),
            "last_execution": self.executions[-1] if self.executions else None,
            "external_side_effects": False,
        }
