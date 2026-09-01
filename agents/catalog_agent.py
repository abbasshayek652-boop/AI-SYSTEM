from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai.base_agent import Agent


class CatalogAgent(Agent):
    """Safe runtime shell for catalog capabilities not yet integrated.

    A scaffold never claims to perform the advertised business action. It only
    exposes lifecycle/health telemetry until a real implementation replaces it.
    """

    name = "catalog_agent"
    description = "Safe capability scaffold; no external side effects."

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.name = str(config.get("display_name", self.name))
        self.description = str(config.get("description", self.description))
        self.key = str(config.get("key", self.name))
        self.layer = str(config.get("layer", "Unassigned"))
        self.implementation = str(config.get("implementation", "scaffold"))
        self.capabilities = list(config.get("capabilities", []))
        self.running = False
        self.started_at: str | None = None
        self.last_tick_at: str | None = None

    async def start(self) -> None:
        self.running = True
        self.started_at = datetime.now(timezone.utc).isoformat()

    async def stop(self) -> None:
        self.running = False

    async def on_tick(self) -> None:
        if self.running:
            self.last_tick_at = datetime.now(timezone.utc).isoformat()

    async def status(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "layer": self.layer,
            "implementation": self.implementation,
            "capabilities": self.capabilities,
            "running": self.running,
            "healthy": True,
            "external_side_effects": False,
            "started_at": self.started_at,
            "last_tick_at": self.last_tick_at,
            "message": "Scaffold only; replace with a real implementation before enabling business execution.",
        }
