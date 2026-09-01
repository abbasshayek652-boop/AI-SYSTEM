from __future__ import annotations

import datetime as dt
from typing import Any

from ai.base_agent import Agent


class LinkedInAgent(Agent):
    """Runtime-safe LinkedIn agent.

    Publishing remains disabled until an explicit LinkedIn OAuth configuration
    is supplied. The agent can still create and inspect local drafts.
    """

    name = "LinkedIn Agent"
    description = "LinkedIn content and publishing workflow"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.running = False
        self.started_at: str | None = None
        self.drafts: list[dict[str, Any]] = []

    async def start(self) -> None:
        self.running = True
        self.started_at = dt.datetime.now(dt.timezone.utc).isoformat()

    async def stop(self) -> None:
        self.running = False

    async def status(self) -> dict[str, Any]:
        return {
            "healthy": True,
            "runtime": "local",
            "publishing_enabled": False,
            "external_side_effects": False,
            "draft_count": len(self.drafts),
            "started_at": self.started_at,
        }

    async def on_tick(self) -> None:
        return None

    async def execute(self, action: str = "inspect", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        if action == "draft":
            draft = {"text": str(payload.get("text", "")), "created_at": dt.datetime.now(dt.timezone.utc).isoformat()}
            self.drafts.append(draft)
            return {"ok": True, "draft": draft, "published": False}
        if action == "publish":
            return {"ok": False, "published": False, "reason": "Publishing is disabled until OAuth is configured and explicitly enabled."}
        return await self.status()
