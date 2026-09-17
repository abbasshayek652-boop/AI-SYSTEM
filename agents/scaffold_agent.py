from __future__ import annotations

from typing import Any

from ai.base_agent import Agent


class ScaffoldAgent(Agent):
    """Safe placeholder for a catalog capability."""

    name = "Scaffold Agent"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.capability_key = str(self.config.get("capability_key", "unknown"))

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    async def status(self) -> dict[str, Any]:
        return {
            "key": self.capability_key,
            "running": self.running,
            "implementation": "scaffold",
            "external_side_effects": False,
        }
