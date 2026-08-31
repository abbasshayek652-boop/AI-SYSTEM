from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Dict

from ai.base_agent import Agent

LOGGER = logging.getLogger(__name__)


class Supervisor:
    """Coordinates agent lifecycle and periodic execution safely."""

    def __init__(self, agents: Dict[str, Agent]) -> None:
        self.agents = agents
        self.tasks: Dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()

    def task_state(self, key: str) -> str:
        task = self.tasks.get(key)
        if task is None:
            return "stopped"
        if task.cancelled():
            return "stopping"
        if task.done():
            return "failed"
        return "running"

    async def start(self, key: str) -> None:
        async with self._lock:
            if key not in self.agents:
                raise KeyError(key)
            task = self.tasks.get(key)
            if task is not None and not task.done():
                LOGGER.info("Agent %s already started", key)
                return
            self.tasks.pop(key, None)
            agent = self.agents[key]
            if not agent.running:
                LOGGER.info("Starting agent %s", key)
                await agent.start()
            else:
                LOGGER.info("Agent %s already running; rebuilding supervisor task", key)
            self.tasks[key] = asyncio.create_task(
                self._tick_loop(key, agent), name=f"mother-ai:{key}"
            )

    async def stop(self, key: str) -> None:
        async with self._lock:
            if key not in self.agents:
                raise KeyError(key)
            LOGGER.info("Stopping agent %s", key)
            task = self.tasks.pop(key, None)
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            await self.agents[key].stop()

    async def stop_all(self) -> None:
        LOGGER.info("Stopping all agents")
        async with self._lock:
            keys = list(self.agents.keys())
        await asyncio.gather(*(self.stop(k) for k in keys), return_exceptions=True)

    async def _tick_loop(self, key: str, agent: Agent) -> None:
        interval = max(1, int(agent.config.get("tick_seconds", 5)))
        LOGGER.info("Starting tick loop for %s with interval %s", key, interval)
        current = asyncio.current_task()
        try:
            while True:
                if agent.running:
                    try:
                        await agent.on_tick()
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:  # noqa: BLE001
                        if hasattr(agent, "last_error"):
                            agent.last_error = str(exc)
                        agent.running = False
                        LOGGER.exception("Agent %s tick failed", key)
                        return
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            LOGGER.info("Tick loop for %s cancelled", key)
            raise
        finally:
            if self.tasks.get(key) is current:
                self.tasks.pop(key, None)
            if not agent.running:
                LOGGER.info("Tick loop for %s exited", key)
