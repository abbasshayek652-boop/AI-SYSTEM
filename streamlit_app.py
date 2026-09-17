"""Mother AI Streamlit control plane.

The UI owns presentation only. FastAPI remains the single control-plane API.
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
EXPECTED_API_VERSION = os.getenv("MOTHER_API_VERSION", "2.2")
STARTUP_TIMEOUT_SECONDS = float(os.getenv("MOTHER_BACKEND_STARTUP_TIMEOUT", "30"))

# Streamlit reruns the script for every interaction. Module globals survive those
# reruns within the same Streamlit process, unlike st.session_state, so the
# backend process is shared by all browser sessions in this app instance.
_BACKEND_PROCESS: subprocess.Popen[bytes] | None = None
_BACKEND_LOG_HANDLE: Any | None = None


class Client:
    def __init__(self, token: str | None = None):
        self.token = token

    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = httpx.request(method, f"{API_BASE}{path}", json=payload, headers=self.headers(), timeout=30)
            if response.is_error:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                return {"error": f"HTTP {response.status_code}: {detail}"}
            return response.json()
        except httpx.HTTPError as exc:
            return {"error": f"Gateway unavailable: {exc}"}

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

    def get(self, path: str) -> dict[str, Any]:
        return self.request("GET", path)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("POST", path, payload)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _lock_pid() -> int | None:
    try:
        return int(LOCK_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _release_lock() -> None:
    try:
        LOCK_FILE.unlink()
    except OSError:
        pass


def _healthy() -> bool:
    try:
        response = httpx.get(f"{API_BASE}/healthz", timeout=2)
        if not response.is_success:
            return False
        payload = response.json()
        return payload.get("api_version") == EXPECTED_API_VERSION
    except (httpx.HTTPError, ValueError):
        return False


def _cleanup_failed_process(process: subprocess.Popen[bytes]) -> None:
    global _BACKEND_PROCESS, _BACKEND_LOG_HANDLE
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if _BACKEND_LOG_HANDLE is not None:
        try:
            _BACKEND_LOG_HANDLE.close()
        except OSError:
            pass
    _BACKEND_PROCESS = None
    _BACKEND_LOG_HANDLE = None


def ensure_backend() -> None:
    global _BACKEND_PROCESS, _BACKEND_LOG_HANDLE

    if _BACKEND_PROCESS is not None:
        if _BACKEND_PROCESS.poll() is None:
            if _healthy():
                return
        else:
            _cleanup_failed_process(_BACKEND_PROCESS)

    # A gateway may already be running independently of this Streamlit process.
    if _healthy():
        return

    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            # Store the Streamlit process PID as the lock owner. The lock is held
            # only for startup and is released after the shared gateway is healthy.
            handle.write(str(os.getpid()))
        owner = True
    except FileExistsError:
        owner = False
        pid = _lock_pid()
        if pid is None or not _pid_alive(pid):
            _release_lock()
            return ensure_backend()

    if not owner:
        deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if _healthy():
                return
            time.sleep(0.25)
        raise RuntimeError(f"Gateway did not become healthy on {API_BASE} within {STARTUP_TIMEOUT_SECONDS:g}s")

    try:
        # Re-check after acquiring the lock because another process could have
        # completed startup between the first health check and lock creation.
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
        _BACKEND_PROCESS = process
        _BACKEND_LOG_HANDLE = log_handle

        deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if _healthy():
                return
            if process.poll() is not None:
                raise RuntimeError(f"Mother AI gateway exited during startup. See {LOG_FILE}.")
            time.sleep(0.25)

        raise RuntimeError(f"Mother AI gateway did not become healthy on {API_BASE} within {STARTUP_TIMEOUT_SECONDS:g}s")
    except Exception:
        if _BACKEND_PROCESS is not None:
            _cleanup_failed_process(_BACKEND_PROCESS)
        else:
            try:
                log_handle.close()  # type: ignore[possibly-undefined]
            except (NameError, OSError):
                pass
        raise
    finally:
        _release_lock()


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
    st.caption("Executive AI orchestration and control plane")
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
catalog_payload = client.get("/catalog")
executive = client.get("/executive/status")

results = {"health": health, "ready": ready, "status": status_payload, "agents": agent_payload, "catalog": catalog_payload, "executive": executive}
errors = {name: value["error"] for name, value in results.items() if isinstance(value, dict) and "error" in value}
if errors:
    st.error("The gateway is reachable but one or more control-plane requests failed.")
    for name, error in errors.items():
        st.warning(f"{name}: {error}")

st.title("🤖 Mother AI Control Plane")
st.caption(f"{st.session_state.email} · {st.session_state.role} · API {health.get('api_version', 'unknown')}")

if st.button("↻ Refresh", use_container_width=False):
    st.rerun()

runtime_agents = agent_payload.get("agents", []) if isinstance(agent_payload.get("agents"), list) else []
catalog_agents = catalog_payload.get("agents", []) if isinstance(catalog_payload.get("agents"), list) else []

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Gateway", "ONLINE" if "error" not in health else "OFFLINE")
m2.metric("System", "READY" if ready.get("ready") else "NOT READY")
m3.metric("Catalog", int(catalog_payload.get("count", 0)))
m4.metric("Runtime", int(catalog_payload.get("loaded_count", len(runtime_agents))))
m5.metric("Running", int(catalog_payload.get("running_count", 0)))

circuit = status_payload.get("circuit_breaker", {})
if isinstance(circuit, dict) and circuit.get("open"):
    st.error("⚠️ Control circuit is OPEN. Agent operations are blocked.")

st.divider()
tab_runtime, tab_catalog, tab_executive, tab_health = st.tabs(["Runtime Agents", "Complete Catalog", "Mother Executive", "System Health"])

with tab_runtime:
    st.subheader("Runtime Agents")
    st.caption("Only agents loaded by registry.json appear here. Catalog-only capabilities are shown separately.")
    if not runtime_agents:
        st.info("No runtime agents are loaded.")
    for row in range(0, len(runtime_agents), 2):
        cols = st.columns(2)
        for column, agent in zip(cols, runtime_agents[row : row + 2]):
            with column:
                key = str(agent.get("key", "unknown"))
                running = bool(agent.get("running"))
                healthy_agent = bool(agent.get("healthy", False))
                mode = agent.get("mode") or (agent.get("registry") or {}).get("config", {}).get("mode") or "standard"
                state = "RUNNING" if running else "STOPPED"
                if not healthy_agent:
                    state = "DEGRADED"
                with st.container(border=True):
                    st.markdown(f"### {agent.get('name', key).title()}")
                    st.caption(f"{agent.get('class_name', 'Agent')} · {agent.get('layer', 'Runtime')} · mode: {mode}")
                    st.metric("State", state)
                    if agent.get("description"):
                        st.write(agent["description"])
                    if agent.get("status_error"):
                        st.warning(agent["status_error"])
                    b1, b2 = st.columns(2)
                    can_control = st.session_state.role in {"operator", "admin"}
                    with b1:
                        if st.button("▶ Start", key=f"start_{key}", disabled=running or not can_control, use_container_width=True):
                            result = client.post("/start", {"agent_key": key})
                            if "error" in result: st.error(result["error"])
                            else: st.success(f"{key} started"); time.sleep(0.3); st.rerun()
                    with b2:
                        if st.button("■ Stop", key=f"stop_{key}", disabled=not running or not can_control, use_container_width=True):
                            result = client.post("/stop", {"agent_key": key})
                            if "error" in result: st.error(result["error"])
                            else: st.success(f"{key} stopped"); time.sleep(0.3); st.rerun()

with tab_catalog:
    st.subheader("Complete Agent Catalog v1.0")
    st.caption("50 planned capabilities. 'Scaffold' means the interface exists conceptually but has no business side effects yet.")
    layer_filter = st.selectbox("Layer", ["All"] + list(dict.fromkeys(str(a.get("layer")) for a in catalog_agents)))
    filtered = [a for a in catalog_agents if layer_filter == "All" or a.get("layer") == layer_filter]
    for agent in filtered:
        runtime = agent.get("runtime", {})
        implementation = agent.get("implementation", "scaffold")
        status = "RUNNING" if runtime.get("running") else ("LOADED" if runtime.get("loaded") else implementation.upper())
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"**{agent['name']}**  ·  `{agent['key']}`")
                st.caption(f"{agent['layer']} · {agent['role']}")
                st.write(" · ".join(agent.get("capabilities", [])))
            with right:
                st.metric("Status", status)

with tab_executive:
    st.subheader("Mother Executive")
    st.json(executive)
    if st.session_state.role in {"operator", "admin"}:
        st.markdown("#### Create decision")
        objective = st.text_area("Objective")
        targets = st.multiselect("Target runtime agents", [a.get("key") for a in runtime_agents])
        priority = st.slider("Priority", 0, 100, 50)
        action = st.text_input("Action", "plan")
        if st.button("Create decision", type="primary"):
            result = client.post("/executive/decide", {"objective": objective, "target_agents": targets, "priority": priority, "action": action})
            if "error" in result: st.error(result["error"])
            else: st.success(f"Decision created: {result.get('id')}"); st.json(result)

with tab_health:
    st.subheader("System Health")
    st.json({"health": health, "readiness": ready, "status": status_payload, "catalog": {"count": catalog_payload.get("count"), "loaded": catalog_payload.get("loaded_count")}, "executive": executive})
    with st.expander("Backend diagnostics"):
        if LOG_FILE.exists():
            lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
            st.code("\n".join(lines[-100:]), language="text")
        else:
            st.info("No backend log file yet.")
    with st.expander("Raw catalog JSON"):
        st.code(json.dumps(catalog_payload, indent=2, default=str), language="json")

st.divider()
if st.button("Logout"):
    for key in ("authenticated", "token", "email", "role"):
        st.session_state[key] = False if key == "authenticated" else None
    st.rerun()
