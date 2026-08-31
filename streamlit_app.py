"""Mother AI Streamlit control plane.

The Streamlit process owns the UI while the FastAPI gateway runs on a private
loopback port. The UI talks only to the gateway API and never imports agent
implementation details directly.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Any

import httpx
import streamlit as st


st.set_page_config(page_title="Mother AI Control Plane", page_icon="🤖", layout="wide")

try:
    for key, value in st.secrets.items():
        os.environ.setdefault(key, str(value))
except Exception:
    pass

BACKEND_HOST = os.getenv("MOTHER_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("MOTHER_BACKEND_PORT", "8001"))
API_BASE = os.getenv("API_BASE", f"http://{BACKEND_HOST}:{BACKEND_PORT}").rstrip("/")
LOCK_FILE = pathlib.Path(os.getenv("MOTHER_BACKEND_LOCK", ".mother_ai_backend.lock"))
LOG_FILE = pathlib.Path(os.getenv("MOTHER_BACKEND_LOG", "mother_ai_backend.log"))


class Client:
    def __init__(self, token: str | None = None):
        self.token = token

    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, api_key: str, email: str, role: str) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{API_BASE}/auth/login",
                json={"email": email, "role": role},
                headers={"X-API-Key": api_key},
                timeout=15,
            )
            if response.is_error:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            return response.json()
        except httpx.HTTPError as exc:
            return {"error": f"Gateway unavailable: {exc}"}

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                f"{API_BASE}{path}",
                json=payload,
                headers=self.headers(),
                timeout=30,
            )
            if response.is_error:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                return {"error": f"HTTP {response.status_code}: {detail}"}
            return response.json()
        except httpx.HTTPError as exc:
            return {"error": f"Gateway unavailable: {exc}"}

    def get(self, path: str) -> dict[str, Any]:
        return self.request("GET", path)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("POST", path, payload)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _read_lock_pid() -> int | None:
    try:
        return int(LOCK_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _acquire_start_lock() -> bool:
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        return True
    except FileExistsError:
        pid = _read_lock_pid()
        if pid is None or not _pid_alive(pid):
            try:
                LOCK_FILE.unlink()
            except OSError:
                return False
            return _acquire_start_lock()
        return False


def _release_start_lock() -> None:
    try:
        LOCK_FILE.unlink()
    except OSError:
        pass


def _healthy() -> bool:
    try:
        response = httpx.get(f"{API_BASE}/healthz", timeout=2)
        return response.is_success
    except httpx.HTTPError:
        return False


def ensure_backend() -> None:
    process = st.session_state.get("backend_process")
    if process is not None and process.poll() is None:
        return

    if _healthy():
        st.session_state["backend_started"] = False
        return

    acquired = _acquire_start_lock()
    if not acquired:
        # Another Streamlit session/process is starting the gateway. Wait for it
        # instead of launching a competing server on the same port.
        for _ in range(30):
            if _healthy():
                st.session_state["backend_started"] = False
                return
            time.sleep(0.25)
        raise RuntimeError(f"Gateway did not become healthy on {API_BASE}")

    try:
        if _healthy():
            return
        env = os.environ.copy()
        env["PORT"] = str(BACKEND_PORT)
        log_handle = LOG_FILE.open("a", encoding="utf-8")
        process = subprocess.Popen(
            [sys.executable, "-m", "mother_ai.run"],
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
        st.session_state["backend_process"] = process
        st.session_state["backend_log_handle"] = log_handle
        for _ in range(40):
            if _healthy():
                st.session_state["backend_started"] = True
                return
            if process.poll() is not None:
                raise RuntimeError(
                    f"Mother AI gateway exited during startup. See {LOG_FILE} for details."
                )
            time.sleep(0.25)
        process.terminate()
        raise RuntimeError(f"Mother AI gateway did not become healthy on {API_BASE}")
    finally:
        _release_start_lock()


try:
    ensure_backend()
except Exception as exc:
    st.error(f"Gateway startup failed: {exc}")
    st.code(str(exc))
    st.stop()


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.role = None


if not st.session_state.authenticated:
    st.title("🤖 Mother AI")
    st.caption("Secure AI orchestration and agent control plane")
    with st.form("login"):
        api_key = st.text_input("API Key", type="password")
        email = st.text_input("Email")
        role = st.selectbox("Role", ["viewer", "operator", "admin"])
        submit = st.form_submit_button("Sign in", use_container_width=True, type="primary")
    if submit:
        if not api_key.strip() or not email.strip():
            st.error("API key and email are required.")
        else:
            result = Client().login(api_key.strip(), email.strip(), role)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.authenticated = True
                st.session_state.token = result["token"]
                st.session_state.email = email.strip()
                st.session_state.role = role
                st.rerun()
    st.caption(f"Gateway: {API_BASE}")
    st.stop()


client = Client(st.session_state.token)
health = client.get("/healthz")
ready = client.get("/readyz")
status_payload = client.get("/status")
agent_payload = client.get("/agents")

if any("error" in result for result in (health, ready, status_payload, agent_payload)):
    st.error("The gateway is reachable but one or more control-plane requests failed.")
    for name, result in (("health", health), ("ready", ready), ("status", status_payload), ("agents", agent_payload)):
        if "error" in result:
            st.warning(f"{name}: {result['error']}")

st.title("🤖 Mother AI Control Plane")
st.caption(f"{st.session_state.email} · {st.session_state.role} · {API_BASE}")

header_left, header_right = st.columns([5, 1])
with header_right:
    if st.button("↻ Refresh", use_container_width=True):
        st.rerun()
if st.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.role = None
    st.rerun()

agents = agent_payload.get("agents", []) if isinstance(agent_payload.get("agents"), list) else []

st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Gateway", "ONLINE" if "error" not in health else "OFFLINE")
m2.metric("System", "READY" if ready.get("ready") else "NOT READY")
m3.metric("Agents", int(agent_payload.get("count", len(agents))))
m4.metric("Running", int(agent_payload.get("running_count", 0)))

circuit = status_payload.get("circuit_breaker", {})
if isinstance(circuit, dict) and circuit.get("open"):
    st.error("⚠️ Control circuit is OPEN. Agent start/stop operations are blocked.")

st.divider()
st.subheader("Agents")
st.caption("Agent controls operate through the authenticated FastAPI supervisor.")

if not agents:
    st.info("No agents are currently loaded. Check /readyz and registry.json.")
else:
    for row in range(0, len(agents), 2):
        columns = st.columns(2)
        for column, agent in zip(columns, agents[row : row + 2]):
            with column:
                key = str(agent.get("key", "unknown"))
                running = bool(agent.get("running"))
                healthy_agent = bool(agent.get("healthy", False))
                mode = agent.get("mode") or (agent.get("registry") or {}).get("config", {}).get("mode") or "standard"
                class_name = agent.get("class_name", "Agent")
                state = "RUNNING" if running else "STOPPED"
                if not healthy_agent:
                    state = "DEGRADED"

                with st.container(border=True):
                    title_col, state_col = st.columns([3, 1])
                    with title_col:
                        st.markdown(f"### {key.title()}")
                        st.caption(f"{class_name} · mode: {mode}")
                    with state_col:
                        st.metric("State", state)

                    if agent.get("description"):
                        st.write(agent["description"])

                    last_error = agent.get("last_error") or agent.get("status_error")
                    if last_error:
                        st.warning(f"Last error: {last_error}")

                    last_tick = agent.get("last_tick_ts")
                    if last_tick:
                        st.caption(f"Last tick: {last_tick}")

                    b1, b2 = st.columns(2)
                    can_control = st.session_state.role in {"operator", "admin"}
                    with b1:
                        if st.button("▶ Start", key=f"start_{key}", disabled=running or not can_control, use_container_width=True):
                            result = client.post("/start", {"agent_key": key})
                            if "error" in result:
                                st.error(result["error"])
                            else:
                                st.success(f"{key} started")
                                time.sleep(0.3)
                                st.rerun()
                    with b2:
                        if st.button("■ Stop", key=f"stop_{key}", disabled=not running or not can_control, use_container_width=True):
                            result = client.post("/stop", {"agent_key": key})
                            if "error" in result:
                                st.error(result["error"])
                            else:
                                st.success(f"{key} stopped")
                                time.sleep(0.3)
                                st.rerun()

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("System Health")
    health_view = {
        "gateway": health,
        "readiness": ready,
        "agent_count": agent_payload.get("count", 0),
        "running_count": agent_payload.get("running_count", 0),
        "healthy_count": agent_payload.get("healthy_count", 0),
    }
    st.json(health_view)

with right:
    st.subheader("Control & Audit")
    st.json({
        "circuit_breaker": circuit,
        "last_audit_ts": status_payload.get("last_audit_ts"),
        "timestamp": status_payload.get("timestamp"),
    })

with st.expander("Raw agent data"):
    st.code(json.dumps(agent_payload, indent=2, default=str), language="json")

with st.expander("Backend diagnostics"):
    st.caption(f"Backend log: {LOG_FILE}")
    if LOG_FILE.exists():
        try:
            lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
            st.code("\n".join(lines[-100:]) or "No backend log output yet.", language="text")
        except OSError as exc:
            st.warning(str(exc))
    else:
        st.info("No backend log file has been created yet.")
