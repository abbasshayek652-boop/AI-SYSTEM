from __future__ import annotations

import asyncio
import uuid

import gateway
from fastapi import Request
from gateway import Command
from gateway.auth import issue_jwt, require


def make_request(path: str, payload: dict[str, object] | None = None) -> Request:
    request = Request({"type": "http", "method": "POST", "path": path, "headers": [], "query_string": b"", "client": ("test", 0), "server": ("test", 80), "scheme": "http", "root_path": "", "http_version": "1.1", "app": gateway.app})
    request.state.correlation_id = str(uuid.uuid4())
    if payload is not None:
        request._test_payload = payload  # type: ignore[attr-defined]
    return request


class JsonRequest(Request):
    def __init__(self, path: str, payload: dict[str, object]) -> None:
        super().__init__({"type": "http", "method": "POST", "path": path, "headers": [], "query_string": b"", "client": ("test", 0), "server": ("test", 80), "scheme": "http", "root_path": "", "http_version": "1.1", "app": gateway.app})
        self.state.correlation_id = str(uuid.uuid4())
        self._payload = payload

    async def json(self) -> dict[str, object]:
        return self._payload


def test_rbac_controls() -> None:
    async def runner() -> None:
        viewer_token = issue_jwt("viewer@example.com", "viewer")
        viewer_request = make_request("/start")
        viewer_dep = require("operator")
        try:
            await viewer_dep(viewer_request, authorization=f"Bearer {viewer_token}", x_api_key=None)
        except Exception as exc:  # noqa: BLE001
            assert getattr(exc, "status_code", None) == 403
        else:
            raise AssertionError("viewer should not pass operator guard")

        operator_token = issue_jwt("operator@example.com", "operator")
        operator_request = make_request("/start")
        operator_ctx = await viewer_dep(operator_request, authorization=f"Bearer {operator_token}", x_api_key=None)
        start_result = await gateway.start_agent(Command(agent_key="learning"), operator_request, operator_ctx)
        assert start_result["ok"] is True
        stop_result = await gateway.stop_agent(Command(agent_key="learning"), operator_request, operator_ctx)
        assert stop_result["ok"] is True

        admin_token = issue_jwt("admin@example.com", "admin")
        admin_request = JsonRequest("/registry/validate", {"agents": []})
        admin_dep = require("admin")
        admin_ctx = await admin_dep(admin_request, authorization=f"Bearer {admin_token}", x_api_key=None)
        validate = await gateway.registry_validate(admin_request, admin_ctx)
        assert validate["ok"] is True
        dryrun = await gateway.registry_dryrun(JsonRequest("/registry/dryrun", {"agents": []}), admin_ctx)
        assert dryrun["ok"] is True

    asyncio.run(runner())
