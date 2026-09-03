from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ConnectionDefinition:
    key: str
    name: str
    category: str
    description: str
    credential_env: tuple[str, ...] = ()
    agent_keys: tuple[str, ...] = ()


CONNECTIONS: tuple[ConnectionDefinition, ...] = (
    ConnectionDefinition(
        key="binance",
        name="Binance",
        category="Finance / Trading",
        description="Exchange account connection. Read-only integration is the first planned live mode.",
        credential_env=("BINANCE_API_KEY", "BINANCE_API_SECRET"),
        agent_keys=("crypto", "portfolio", "risk"),
    ),
    ConnectionDefinition(
        key="linkedin",
        name="LinkedIn",
        category="Content",
        description="Professional publishing account. Draft and approval workflow comes before publishing.",
        credential_env=("LINKEDIN_ACCESS_TOKEN",),
        agent_keys=("linkedin", "content"),
    ),
    ConnectionDefinition(
        key="telegram",
        name="Telegram",
        category="Communication",
        description="Notifications and operational alerts.",
        credential_env=("TELEGRAM_BOT_TOKEN",),
        agent_keys=("notification",),
    ),
    ConnectionDefinition(
        key="github",
        name="GitHub",
        category="Development",
        description="Repository and development automation connection.",
        credential_env=("GITHUB_TOKEN",),
        agent_keys=("github", "testing", "documentation"),
    ),
)


def _configured(definition: ConnectionDefinition) -> bool:
    return bool(definition.credential_env) and all(os.getenv(name, "").strip() for name in definition.credential_env)


def connection_statuses(runtime_agents: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    runtime_agents = runtime_agents or {}
    result: list[dict[str, Any]] = []
    for definition in CONNECTIONS:
        configured = _configured(definition)
        related = []
        for key in definition.agent_keys:
            agent = runtime_agents.get(key)
            if agent is not None:
                related.append({
                    "key": key,
                    "running": bool(getattr(agent, "running", False)),
                })
        item = asdict(definition)
        item["credential_env"] = list(definition.credential_env)
        item["agent_keys"] = list(definition.agent_keys)
        item["configured"] = configured
        item["status"] = "CONFIGURED" if configured else "NOT_CONFIGURED"
        item["integration_mode"] = "adapter_pending"
        item["agents"] = related
        result.append(item)
    return result
