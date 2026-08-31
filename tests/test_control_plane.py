from __future__ import annotations

import asyncio

from ai.base_agent import Agent
from ai.supervisor import Supervisor
from routers.core import _safe_agent_status


class HealthyAgent(Agent):
    name = "healthy"
    description = "test agent"

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    async def status(self) -> dict[str, object]:
        return {"running": self.running, "last_tick_ts": 123}


class BrokenStatusAgent(HealthyAgent):
    async def status(self) -> dict[str, object]:
        raise RuntimeError("status unavailable")


class BrokenTickAgent(HealthyAgent):
    async def on_tick(self) -> None:
        raise RuntimeError("tick failed")


def test_safe_status_isolated_from_agent_failure() -> None:
    async def run() -> None:
        key, payload = await _safe_agent_status("broken", BrokenStatusAgent({"tick_seconds": 1}))
        assert key == "broken"
        assert payload["healthy"] is False
        assert payload["status_error"] == "status unavailable"

    asyncio.run(run())


def test_supervisor_removes_failed_tick_task() -> None:
    async def run() -> None:
        agent = BrokenTickAgent({"tick_seconds": 1})
        supervisor = Supervisor({"broken": agent})
        await supervisor.start("broken")
        await asyncio.sleep(0.05)
        assert agent.running is False
        assert "broken" not in supervisor.tasks
        await supervisor.stop_all()

    asyncio.run(run())


def test_supervisor_can_restart_after_tick_failure() -> None:
    async def run() -> None:
        agent = BrokenTickAgent({"tick_seconds": 1})
        supervisor = Supervisor({"broken": agent})
        await supervisor.start("broken")
        await asyncio.sleep(0.05)
        await supervisor.start("broken")
        assert "broken" in supervisor.tasks
        await supervisor.stop("broken")

    asyncio.run(run())
