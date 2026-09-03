from __future__ import annotations

import os
from typing import Any

import httpx


def api_base() -> str:
    return os.getenv("API_BASE", f"http://{os.getenv('MOTHER_BACKEND_HOST', '127.0.0.1')}:{os.getenv('MOTHER_BACKEND_PORT', '8001')}").rstrip("/")


def get(path: str, token: str | None, **params: Any) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = httpx.get(f"{api_base()}{path}", headers=headers, params=params or None, timeout=15)
    response.raise_for_status()
    return response.json()


def require_auth(st: Any) -> str:
    if not st.session_state.get("authenticated"):
        st.warning("Sign in from the Mother AI home page first.")
        st.stop()
    return str(st.session_state.get("token"))
