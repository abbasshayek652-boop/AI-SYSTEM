from __future__ import annotations

from integrations.base import ConnectionHealth
from integrations.env_adapter import EnvConnectionAdapter


def test_connection_health_public_dict_contains_no_credentials() -> None:
    health = ConnectionHealth(
        key="example",
        configured=True,
        reachable=True,
        authenticated=True,
        capabilities=("account.read",),
    )
    payload = health.public_dict()
    assert payload["healthy"] is True
    assert "api_key" not in payload
    assert "secret" not in payload


def test_env_adapter_is_not_network_side_effecting(monkeypatch) -> None:
    monkeypatch.delenv("TEST_TOKEN", raising=False)
    adapter = EnvConnectionAdapter("example", ("TEST_TOKEN",), ("read",))
    health = adapter.health_check()
    assert health.configured is False
    assert health.reachable is False
    assert health.authenticated is False
