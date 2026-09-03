from __future__ import annotations

from gateway import app


def test_control_plane_routes_exist() -> None:
    paths = app.openapi()["paths"]
    assert "/agents" in paths and "get" in paths["/agents"]
    assert "/agents/{agent_key}" in paths and "get" in paths["/agents/{agent_key}"]
    assert "/start" in paths and "post" in paths["/start"]
    assert "/stop" in paths and "post" in paths["/stop"]
    assert "/healthz" in paths and "get" in paths["/healthz"]
    assert "/readyz" in paths and "get" in paths["/readyz"]
    assert "/status" in paths and "get" in paths["/status"]
    assert "/integrations/health" in paths and "get" in paths["/integrations/health"]
    assert "/approvals" in paths and "get" in paths["/approvals"]
    assert "/policy" in paths and "get" in paths["/policy"]


def test_application_exposes_expected_agent_contract() -> None:
    assert app.title == "Mother AI Gateway"
    assert app.version == "2.2.0"
    assert hasattr(app.state, "limiter")
