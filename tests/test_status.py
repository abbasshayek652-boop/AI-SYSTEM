from __future__ import annotations

import asyncio

from starlette.requests import Request

import gateway
from gateway.auth import AuthContext
from routers.core import status_endpoint


def _make_request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/status", "headers": [], "query_string": b"", "client": ("test", 0), "server": ("test", 80), "scheme": "http", "root_path": "", "http_version": "1.1", "app": gateway.app})


def test_status() -> None:
    ctx = AuthContext(user_id="tester", role="viewer")
    payload = asyncio.run(status_endpoint(_make_request(), ctx))
    assert "loaded_agents" in payload
    assert "running" in payload
    assert isinstance(payload["loaded_agents"], list)
    assert isinstance(payload["running"], dict)
