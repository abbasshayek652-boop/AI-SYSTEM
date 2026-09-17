from __future__ import annotations

import asyncio

from starlette.requests import Request

import gateway
from routers.core import healthz


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/healthz", "headers": [], "query_string": b"", "client": ("test", 0), "server": ("test", 80), "scheme": "http", "root_path": "", "http_version": "1.1", "app": gateway.app})


def test_healthz() -> None:
    payload = asyncio.run(healthz(_request()))
    assert payload["ok"] is True
    assert payload["service"] == "mother_ai"
    assert payload["api_version"] == gateway.app.state.api_version
    assert "timestamp" in payload
