from __future__ import annotations

import asyncio
import uuid

import gateway
from fastapi import Request
from gateway import Command
from gateway.auth import issue_jwt, require


def make_request(correlation_id: str) -> Request:
    return Request({"type": "http", "method": "POST", "path": "/start", "headers": [], "query_string": b"", "client": ("test", 0), "server": ("test", 80), "scheme": "http", "root_path": "", "http_version": "1.1", "app": gateway.app})


def test_rate_limit_and_idempotency() -> None:
    async def runner() -> None:
        operator_token = issue_jwt("rate@example.com", "operator")
        dependency = require("operator")

        async def invoke() -> dict[str, object]:
            request = make_request(str(uuid.uuid4()))
            request.state.correlation_id = str(uuid.uuid4())
            ctx = await dependency(request, authorization=f"Bearer {operator_token}", x_api_key=None)
            return await gateway.start_agent(Command(agent_key="learning"), request, ctx)

        first = await invoke()
        assert first["ok"] is True

        duplicate = await invoke()
        assert duplicate.get("duplicate") is True

        for _ in range(3):
            await invoke()

        try:
            await invoke()
        except Exception as exc:  # noqa: BLE001
            assert getattr(exc, "status_code", None) == 429
        else:
            raise AssertionError("rate limit not enforced")

        stop_request = make_request(str(uuid.uuid4()))
        stop_request.state.correlation_id = str(uuid.uuid4())
        stop_ctx = await dependency(stop_request, authorization=f"Bearer {operator_token}", x_api_key=None)
        await gateway.stop_agent(Command(agent_key="learning"), stop_request, stop_ctx)

    asyncio.run(runner())
