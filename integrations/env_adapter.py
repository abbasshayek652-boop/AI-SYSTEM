from __future__ import annotations

import os
import time

from integrations.base import ConnectionAdapter, ConnectionHealth


class EnvConnectionAdapter(ConnectionAdapter):
    """Generic adapter used until a service-specific API adapter is installed."""

    def __init__(self, key: str, required_env: tuple[str, ...], capabilities: tuple[str, ...] = ()) -> None:
        self.key = key
        self.required_env = required_env
        self.capabilities = capabilities

    def health_check(self) -> ConnectionHealth:
        configured = all(bool(os.getenv(name)) for name in self.required_env)
        return ConnectionHealth(
            key=self.key,
            configured=configured,
            reachable=False,
            authenticated=False,
            error=None if configured else "required configuration is missing",
            checked_at=time.time(),
            capabilities=self.capabilities,
        )
