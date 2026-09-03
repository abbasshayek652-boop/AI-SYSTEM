from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from integrations.bootstrap import register_default_adapters
from integrations.registry import get


@dataclass(frozen=True)
class ConnectionDefinition:
    key: str
    name: str
    category: str
    description: str
    credential_env: tuple[str, ...] = ()
    agent_keys: tuple[str, ...] = ()


CONNECTIONS: tuple[ConnectionDefinition, ...] = (
    ConnectionDefinition("binance", "Binance", "Finance / Trading", "Exchange account. Initial live integration is read-only.", ("BINANCE_API_KEY", "BINANCE_API_SECRET"), ("crypto", "portfolio", "risk")),
    ConnectionDefinition("linkedin", "LinkedIn", "Content", "Professional publishing account. Draft and approval workflow precedes publishing.", ("LINKEDIN_ACCESS_TOKEN",), ("linkedin", "content")),
    ConnectionDefinition("telegram", "Telegram", "Communication", "Notifications and operational alerts.", ("TELEGRAM_BOT_TOKEN",), ("notification",)),
    ConnectionDefinition("github", "GitHub", "Development", "Repository and development automation connection.", ("GITHUB_TOKEN",), ("github", "testing", "documentation")),
)


def _configured(definition: ConnectionDefinition) -> bool:
    import os
    return bool(definition.credential_env) and all(os.getenv(name, "").strip() for name in definition.credential_env)


def connection_statuses(runtime_agents: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    register_default_adapters()
    runtime_agents = runtime_agents or {}
    result: list[dict[str, Any]] = []
    for definition in CONNECTIONS:
        configured = _configured(definition)
        adapter = get(definition.key)
        health = adapter.health_check() if adapter is not None and configured else None
        related = []
        for key in definition.agent_keys:
            agent = runtime_agents.get(key)
            if agent is not None:
                related.append({"key": key, "running": bool(getattr(agent, "running", False))})
        item = asdict(definition)
        item.pop("credential_env", None)
        item["agent_keys"] = list(definition.agent_keys)
        item["configured"] = configured
        item["reachable"] = bool(health.reachable) if health else False
        item["authenticated"] = bool(health.authenticated) if health else False
        item["last_error"] = health.error if health else None
        item["status"] = "HEALTHY" if health and health.healthy else ("CONFIGURED" if configured else "NOT_CONFIGURED")
        item["integration_mode"] = "read_only" if definition.key == "binance" else "adapter_ready"
        item["capabilities"] = list(health.capabilities) if health else []
        item["agents"] = related
        result.append(item)
    return result
