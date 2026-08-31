"""Mother AI Streamlit dashboard.

The Streamlit process owns the UI; the FastAPI gateway is started once on a
separate loopback port. This avoids collisions with Streamlit Cloud's process.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from typing import Any

import httpx
import streamlit as st


st.set_page_config(page_title="Mother AI Network", page_icon="🤖", layout="wide")

# Copy Streamlit secrets into the environment before importing/starting the gateway.
try:
    for key, value in st.secrets.items():
        os.environ.setdefault(key, str(value))
except Exception:
    pass

BACKEND_HOST = os.getenv("MOTHER_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("MOTHER_BACKEND_PORT", "8001"))
API_BASE = os.getenv("API_BASE", f"http://{BACKEND_HOST}:{BACKEND_PORT}").rstrip("/")


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


async def _healthy() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{API_BASE}/healthz")
            return response.is_success
    except Exception:
        return False


def ensure_backend() -> None:
    if st.session_state.get("backend_process") is not None:
        process = st.session_state["backend_process"]
        if process.poll() is None:
            return

    if _run(_healthy()):
        st.session_state["backend_started"] = True
        return

    env = os.environ.copy()
    env["PORT"] = str(BACKEND_PORT)
    process = subprocess.Popen(
        [sys.executable, "-m", "mother_ai.run"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    st.session_state["backend_process"] = process
    for _ in range(20):
        if _run(_healthy()):
            st.session_state["backend_started"] = True
            return
        if process.poll() is not None:
            raise RuntimeError("Mother AI gateway exited during startup")
        time.sleep(0.25)
    raise RuntimeError(f"Mother AI gateway did not become healthy on {API_BASE}")


try:
    ensure_backend()
except Exception as exc:
    st.error(f"Gateway startup failed: {exc}")
    st.stop()


class Client:
    def __init__(self, token: str | None = None):
        self.token = token

    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def login(self, api_key: str, email: str, role: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{API_BASE}/auth/login",
                json={"email": email, "role": role},
                headers={"X-API-Key": api_key},
            )
            if response.is_error:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            return response.json()

    async def get(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{API_BASE}{path}", headers=self.headers())
            if response.is_error:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            return response.json()

    async def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{API_BASE}{path}", json=payload, headers=self.headers())
            if response.is_error:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            return response.json()


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.role = None


if not st.session_state.authenticated:
    st.title("🔐 Mother AI Login")
    with st.form("login"):
        api_key = st.text_input("API Key", type="password")
        email = st.text_input("Email")
        role = st.selectbox("Role", ["viewer", "operator", "admin"])
        submit = st.form_submit_button("Login", use_container_width=True)
    if submit:
        if not api_key or not email:
            st.error("API key and email are required.")
        else:
            result = _run(Client().login(api_key, email, role))
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.authenticated = True
                st.session_state.token = result["token"]
                st.session_state.email = email
                st.session_state.role = role
                st.rerun()
    st.caption(f"Gateway: {API_BASE}")
    st.stop()


client = Client(st.session_state.token)
st.title("🤖 Mother AI Network")
st.caption(f"{st.session_state.email} · {st.session_state.role} · {API_BASE}")

if st.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.token = None
    st.rerun()

health = _run(client.get("/healthz"))
ready = _run(client.get("/readyz"))

c1, c2, c3 = st.columns(3)
c1.metric("Gateway", "ONLINE" if "error" not in health else "OFFLINE")
c2.metric("Ready", str(ready.get("ready", False)))
c3.metric("Agents", len(ready.get("agents", []) if isinstance(ready.get("agents"), list) else []))

st.divider()
st.subheader("Agents")
result = _run(client.get("/agents"))
if "error" in result:
    st.error(result["error"])
else:
    st.json(result)

st.subheader("System Status")
status = _run(client.get("/status"))
if "error" in status:
    st.error(status["error"])
else:
    st.json(status)
