from __future__ import annotations

from integrations.base import ConnectionAdapter, ConnectionHealth


_ADAPTERS: dict[str, ConnectionAdapter] = {}


def register(adapter: ConnectionAdapter) -> None:
    if adapter.key in _ADAPTERS:
        raise ValueError(f"Duplicate integration adapter: {adapter.key}")
    _ADAPTERS[adapter.key] = adapter


def get(key: str) -> ConnectionAdapter | None:
    return _ADAPTERS.get(key)


def all_adapters() -> list[ConnectionAdapter]:
    return list(_ADAPTERS.values())


def health_all() -> list[ConnectionHealth]:
    return [adapter.health_check() for adapter in _ADAPTERS.values()]
