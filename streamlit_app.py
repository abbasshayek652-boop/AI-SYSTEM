"""Mother AI Streamlit control plane.

Streamlit is the UI and owns one local FastAPI gateway process.  The launcher
is deliberately defensive because Streamlit can execute multiple sessions in
the same Linux container; only one gateway may bind the configured port.
"""
from __future__ import annotations

import json
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time
from typing import Any

import httpx
import streamlit as st

st.set_page_config(page_title="Mother AI", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

try:
    for key, value in st.secrets.items():
        os.environ.setdefault(key, str(value))
except Exception:
    pass

BACKEND_HOST = os.getenv("MOTHER_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("MOTHER_BACKEND_PORT", "8001"))
API_BASE = os.getenv("API_BASE", f"http://{BACKEND_HOST}:{BACKEND_PORT}").rstrip("/")
API_VERSION = "2.2"
LOCK_FILE = pathlib.Path(os.getenv("MOTHER_BACKEND_LOCK", ".mother_ai_backend.lock"))
PID_FILE = pathlib.Path(os.getenv("MOTHER_PID_FILE", ".mother_ai_backend.pid"))
LOG_FILE = pathlib.Path(os.getenv("MOTHER_BACKEND_LOG", "mother_ai_backend.log"))


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
            response = httpx.request(method, f"{API_BASE}{path}", json=payload, headers=self.headers(), timeout=20)
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


def _read_pid() -> int | None:
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        return pid if pid > 0 else None
    except (OSError, ValueError):
        return None


def _port_open() -> bool:
    """Return True when something is listening on the configured TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        try:
            return sock.connect_ex((BACKEND_HOST, BACKEND_PORT)) == 0
        except OSError:
            return False


def _kill_backend() -> None:
    """Stop only a gateway recorded by our PID file."""
    pid = _read_pid()
    if pid is not None and pid != os.getpid() and _pid_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        for _ in range(30):
            if not _pid_alive(pid):
                break
            time.sleep(0.1)
    try:
        PID_FILE.unlink()
    except OSError:
        pass


def _kill_port_owner() -> None:
    """Recover a stale listener when no valid PID file exists.

    Streamlit Community Cloud runs on Linux.  ``fuser`` is preferred because it
    targets the configured TCP port instead of blindly killing Python processes.
    """
    try:
        subprocess.run(
            ["fuser", "-k", f"{BACKEND_PORT}/tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        pass
    for _ in range(20):
        if not _port_open():
            return
        time.sleep(0.1)


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
        data = response.json()
        return data.get("api_version") == API_VERSION and data.get("status") in {"ok", "healthy"}
    except (httpx.HTTPError, ValueError):
        return False


def _acquire_lock() -> bool:
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        return True
    except FileExistsError:
        return False


def _recover_stale_lock() -> None:
    """Remove a lock whose recorded owner is no longer alive."""
    try:
        owner = int(LOCK_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        _release_lock()
        return
    if owner != os.getpid() and not _pid_alive(owner):
        _release_lock()


def ensure_backend() -> None:
    process = st.session_state.get("backend_process")
    if process is not None and process.poll() is None and _healthy():
        return

    # First preference: reuse an already healthy gateway.  This prevents every
    # Streamlit rerun/session from trying to launch another uvicorn instance.
    if _healthy():
        return

    # If the previous backend belongs to this application, stop it cleanly.
    _kill_backend()
    _recover_stale_lock()

    # Another Streamlit session may be starting the gateway right now.
    owner = _acquire_lock()
    if not owner:
        for _ in range(80):
            if _healthy():
                return
            _recover_stale_lock()
            if _acquire_lock():
                owner = True
                break
            time.sleep(0.25)
        if not owner:
            raise RuntimeError(f"Another Streamlit session owns the gateway lock and {API_BASE} never became healthy.")

    process = None
    log_handle = None
    try:
        # The port can be occupied by a previous process that has no PID file.
        # Never launch into a known occupied port.
        if _port_open() and not _healthy():
            _kill_port_owner()
        if _port_open():
            raise RuntimeError(f"Gateway port {BACKEND_PORT} is already in use by an unhealthy process.")

        env = os.environ.copy()
        env["PORT"] = str(BACKEND_PORT)
        env["MOTHER_PID_FILE"] = str(PID_FILE)
        env["MOTHER_BACKEND_LOCK"] = str(LOCK_FILE)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        log_handle = LOG_FILE.open("a", encoding="utf-8")
        process = subprocess.Popen(
            [sys.executable, "-m", "mother_ai.run"],
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        st.session_state["backend_process"] = process
        st.session_state["backend_log_handle"] = log_handle

        for _ in range(80):
            if _healthy():
                # Do NOT release the lock here.  The backend owns it for its
                # lifetime and mother_ai.run removes it on process exit.
                return
            if process.poll() is not None:
                tail = ""
                if LOG_FILE.exists():
                    tail = "\n".join(LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()[-30:])
                raise RuntimeError(f"Mother AI gateway exited during startup. See {LOG_FILE}.\n\n{tail}")
            time.sleep(0.25)
        process.terminate()
        raise RuntimeError(f"Mother AI gateway did not become healthy on {API_BASE}")
    except Exception:
        if process is not None and process.poll() is None:
            process.terminate()
        _release_lock()
        raise
    finally:
        if log_handle is not None and process is not None and process.poll() is not None:
            log_handle.close()


try:
    ensure_backend()
except Exception as exc:
    st.error(f"Gateway startup failed: {exc}")
    st.code(str(exc))
    if LOG_FILE.exists():
        st.code("\n".join(LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()[-100:]), language="text")
    st.stop()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.role = None

if not st.session_state.authenticated:
    st.title("🤖 Mother AI")
    st.subheader("Unified AI operating system")
    st.caption("50-agent runtime · local Streamlit deployment · governed execution")
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
    st.caption(f"Gateway: {API_BASE} · API {API_VERSION}")
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

runtime_agents = agent_payload.get("agents", []) if isinstance(agent_payload.get("agents"), list) else []
catalog_agents = catalog_payload.get("agents", []) if isinstance(catalog_payload.get("agents"), list) else []

st.title("🤖 Mother AI")
st.caption(f"{st.session_state.email} · {st.session_state.role} · API {health.get('api_version', 'unknown')}")

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
tab_runtime, tab_catalog, tab_execute, tab_executive, tab_health = st.tabs(["Runtime", "50-Agent Catalog", "Agent Console", "Mother Executive", "System Health"])

with tab_runtime:
    st.subheader(f"Runtime Agents ({len(runtime_agents)})")
    st.caption("All catalog capabilities are loaded as safe local runtime agents. External publishing, trading, and deployment side effects remain explicitly disabled until configured.")
    for row in range(0, len(runtime_agents), 3):
        cols = st.columns(3)
        for column, agent in zip(cols, runtime_agents[row : row + 3]):
            with column:
                key = str(agent.get("key", "unknown"))
                running = bool(agent.get("running"))
                healthy_agent = bool(agent.get("healthy", False))
                state = "RUNNING" if running else "STOPPED"
                if not healthy_agent:
                    state = "DEGRADED"
                with st.container(border=True):
                    st.markdown(f"### {agent.get('name', key)}")
                    st.caption(f"{agent.get('layer', 'Runtime')} · `{key}`")
                    st.metric("State", state)
                    if agent.get("description"):
                        st.write(agent["description"])
                    b1, b2 = st.columns(2)
                    can_control = st.session_state.role in {"operator", "admin"}
                    with b1:
                        if st.button("▶ Start", key=f"start_{key}", disabled=running or not can_control, use_container_width=True):
                            result = client.post("/start", {"agent_key": key})
                            if "error" in result: st.error(result["error"])
                            else: st.success(f"{key} started"); time.sleep(0.2); st.rerun()
                    with b2:
                        if st.button("■ Stop", key=f"stop_{key}", disabled=not running or not can_control, use_container_width=True):
                            result = client.post("/stop", {"agent_key": key})
                            if "error" in result: st.error(result["error"])
                            else: st.success(f"{key} stopped"); time.sleep(0.2); st.rerun()

with tab_catalog:
    st.subheader("Complete Agent Catalog v1.0")
    layer_filter = st.selectbox("Layer", ["All"] + list(dict.fromkeys(str(a.get("layer")) for a in catalog_agents)))
    filtered = [a for a in catalog_agents if layer_filter == "All" or a.get("layer") == layer_filter]
    st.caption(f"Showing {len(filtered)} of {len(catalog_agents)} capabilities")
    for agent in filtered:
        runtime = agent.get("runtime", {})
        loaded = bool(runtime.get("loaded"))
        running = bool(runtime.get("running"))
        status_text = "RUNNING" if running else "READY" if loaded else "CATALOG ONLY"
        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**{agent['name']}** · `{agent['key']}`")
                st.caption(f"{agent['layer']} · {agent['role']}")
                st.write(" · ".join(agent.get("capabilities", [])))
            with right:
                st.metric("Status", status_text)

with tab_execute:
    st.subheader("Agent Console")
    keys = [str(a.get("key")) for a in runtime_agents]
    selected = st.selectbox("Agent", keys if keys else ["none"])
    selected_row = next((a for a in runtime_agents if a.get("key") == selected), {})
    st.caption(f"{selected_row.get('name', selected)} · {selected_row.get('layer', '')}")
    action = st.text_input("Action", "inspect")
    payload_text = st.text_area("Payload JSON", "{}", height=140)
    if st.button("Execute", type="primary", disabled=st.session_state.role not in {"operator", "admin"} or not selected):
        try:
            payload = json.loads(payload_text or "{}")
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a JSON object")
            result = client.post(f"/agents/{selected}/execute", {"action": action, "payload": payload})
            if "error" in result: st.error(result["error"])
            else: st.json(result)
        except (ValueError, json.JSONDecodeError) as exc:
            st.error(f"Invalid payload: {exc}")

with tab_executive:
    st.subheader("Mother Executive")
    st.json(executive)
    if st.session_state.role in {"operator", "admin"}:
        st.markdown("#### Create decision")
        objective = st.text_area("Objective")
        targets = st.multiselect("Target runtime agents", keys)
        priority = st.slider("Priority", 0, 100, 50)
        action = st.text_input("Decision action", "plan")
        if st.button("Create decision", type="primary"):
            result = client.post("/executive/decide", {"objective": objective, "target_agents": targets, "priority": priority, "action": action})
            if "error" in result: st.error(result["error"])
            else: st.success(f"Decision created: {result.get('id')}"); st.json(result)

with tab_health:
    st.subheader("System Health")
    st.json({"health": health, "readiness": ready, "status": status_payload, "runtime_agents": len(runtime_agents), "catalog_agents": len(catalog_agents), "executive": executive})
    with st.expander("Backend diagnostics"):
        if LOG_FILE.exists():
            lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
            st.code("\n".join(lines[-120:]), language="text")
        else:
            st.info("No backend log file yet.")
    with st.expander("Raw catalog JSON"):
        st.code(json.dumps(catalog_payload, indent=2, default=str), language="json")

st.divider()
if st.button("Logout"):
    for key in ("authenticated", "token", "email", "role"):
        st.session_state[key] = False if key == "authenticated" else None
    st.rerun()
