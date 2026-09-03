from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

st.set_page_config(page_title="Mother AI · Connections", page_icon="🔌", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Sign in from the Mother AI home page first.")
    st.stop()

BACKEND_HOST = os.getenv("MOTHER_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("MOTHER_BACKEND_PORT", "8001"))
API_BASE = os.getenv("API_BASE", f"http://{BACKEND_HOST}:{BACKEND_PORT}").rstrip("/")
TOKEN = st.session_state.get("token")
HEADERS = {"Accept": "application/json", "Authorization": f"Bearer {TOKEN}"}


def get_connections() -> dict[str, Any]:
    try:
        response = httpx.get(f"{API_BASE}/observability/connections", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


st.title("🔌 Connections")
st.caption("One control-plane view of the services Mother AI can eventually connect to. Secrets are never displayed here.")

if st.button("↻ Refresh", type="primary"):
    st.rerun()

payload = get_connections()
if "error" in payload:
    st.error(payload["error"])
    st.stop()

items = payload.get("items", [])
configured = int(payload.get("configured_count", 0))

m1, m2, m3 = st.columns(3)
m1.metric("Known connections", len(items))
m2.metric("Configured", configured)
m3.metric("Adapters ready", sum(item.get("integration_mode") == "ready" for item in items))

st.divider()

for row in range(0, len(items), 2):
    cols = st.columns(2)
    for col, item in zip(cols, items[row : row + 2]):
        with col:
            with st.container(border=True):
                status = item.get("status", "UNKNOWN")
                st.subheader(item.get("name", item.get("key", "Unknown")))
                st.caption(item.get("category", ""))
                st.metric("Status", status)
                st.write(item.get("description", ""))
                mode = item.get("integration_mode", "unknown")
                st.caption(f"Integration: `{mode}`")
                agents = item.get("agents", [])
                if agents:
                    st.write("Related runtime agents")
                    for agent in agents:
                        state = "running" if agent.get("running") else "stopped"
                        st.write(f"• `{agent.get('key')}` — {state}")
                else:
                    st.caption("No related runtime agent is currently loaded.")

st.info("Phase 2 intentionally reports configuration only. The next phases add real adapters one service at a time, starting with safe read-only connectivity and explicit approval for side effects.")
