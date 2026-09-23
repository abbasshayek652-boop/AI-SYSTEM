from __future__ import annotations

import os
from typing import Any

import httpx

def api_base() -> str:
    return os.getenv(
        "API_BASE",
        "http://" + os.getenv("MOTHER_BACKEND_HOST", "127.0.0.1") + ":" + os.getenv("MOTHER_BACKEND_PORT", "8001"),
    ).rstrip("/")

def request(method: str, path: str, token: str | None, payload: dict[str, Any] | None = None, **params: Any) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = httpx.request(method, api_base() + path, headers=headers, json=payload, params=params or None, timeout=20)
    response.raise_for_status()
    return response.json()

def get(path: str, token: str | None, **params: Any) -> dict[str, Any]:
    return request("GET", path, token, **params)

def post(path: str, token: str | None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return request("POST", path, token, payload)

def require_auth(st: Any) -> str:
    if not st.session_state.get("authenticated"):
        st.warning("Sign in from the Mother AI home page first.")
        st.stop()
    return str(st.session_state.get("token"))
