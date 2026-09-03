from __future__ import annotations

import asyncio

from starlette.requests import Request

import gateway
from routers.core import readyz


def _make_request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/readyz", "headers": [], "query_string": b"", "client": ("test", 0), "server": ("test", 80), "scheme": "http", "root_path": "", "http_version": "1.1", "app": gateway.app})


def test_readyz() -> None:
    payload = asyncio.run(readyz(_make_request()))
    assert payload["db"] is True
    assert payload["registry"] is True
    assert payload["agents"] is True
    assert payload["ready"] is True
