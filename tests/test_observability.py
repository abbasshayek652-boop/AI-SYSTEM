from __future__ import annotations

import os

from services.connections import connection_statuses


def test_connection_status_does_not_expose_secret_values(monkeypatch):
    monkeypatch.setenv("BINANCE_API_KEY", "secret-key")
    monkeypatch.setenv("BINANCE_API_SECRET", "secret-secret")

    items = connection_statuses({})
    binance = next(item for item in items if item["key"] == "binance")

    assert binance["configured"] is True
    assert binance["status"] == "CONFIGURED"
    assert "secret-key" not in str(binance)
    assert "secret-secret" not in str(binance)
    assert "BINANCE_API_KEY" in binance["credential_env"]


def test_connection_status_is_not_configured_without_credentials(monkeypatch):
    monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)

    items = connection_statuses({})
    linkedin = next(item for item in items if item["key"] == "linkedin")

    assert linkedin["configured"] is False
    assert linkedin["status"] == "NOT_CONFIGURED"
    assert linkedin["integration_mode"] == "adapter_pending"


def test_connection_status_reports_related_runtime_agents():
    class Agent:
        running = True

    items = connection_statuses({"crypto": Agent()})
    binance = next(item for item in items if item["key"] == "binance")

    assert binance["agents"] == [{"key": "crypto", "running": True}]
