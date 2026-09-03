from __future__ import annotations

from gateway import app


def test_control_plane_routes_exist() -> None:
    routes = {(getattr(route, "path", None), tuple(sorted(getattr(route, "methods", set())))) for route in app.routes}
    assert any(path == "/agents" and "GET" in methods for path, methods in routes)
    assert any(path == "/agents/{agent_key}" and "GET" in methods for path, methods in routes)
    assert any(path == "/start" and "POST" in methods for path, methods in routes)
    assert any(path == "/stop" and "POST" in methods for path, methods in routes)
    assert any(path == "/healthz" and "GET" in methods for path, methods in routes)
    assert any(path == "/readyz" and "GET" in methods for path, methods in routes)
    assert any(path == "/status" and "GET" in methods for path, methods in routes)
    assert any(path == "/integrations/health" and "GET" in methods for path, methods in routes)
    assert any(path == "/approvals" and "GET" in methods for path, methods in routes)
    assert any(path == "/policy" and "GET" in methods for path, methods in routes)


def test_application_exposes_expected_agent_contract() -> None:
    assert app.title == "Mother AI Gateway"
    assert app.version == "2.2.0"
    assert hasattr(app.state, "limiter")
