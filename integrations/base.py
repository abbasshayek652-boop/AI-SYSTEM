from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ConnectionHealth:
    key: str
    configured: bool
    reachable: bool = False
    authenticated: bool = False
    error: str | None = None
    checked_at: float | None = None
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    @property
    def healthy(self) -> bool:
        return self.configured and self.reachable and self.authenticated and self.error is None

    def public_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "configured": self.configured,
            "reachable": self.reachable,
            "authenticated": self.authenticated,
            "healthy": self.healthy,
            "error": self.error,
            "checked_at": self.checked_at,
            "capabilities": list(self.capabilities),
        }


class ConnectionAdapter(ABC):
    key: str
    capabilities: tuple[str, ...] = ()

    @abstractmethod
    def health_check(self) -> ConnectionHealth:
        """Return a safe, non-secret connection health result."""
        raise NotImplementedError

    def validate_config(self) -> bool:
        return self.health_check().configured

    def close(self) -> None:
        return None
