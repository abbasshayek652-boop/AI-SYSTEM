from __future__ import annotations

import os
from typing import Any

import httpx
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Mother AI · Activity", page_icon="🛰️", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Sign in from the Mother AI home page first.")
    st.stop()

BACKEND_HOST = os.getenv("MOTHER_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("MOTHER_BACKEND_PORT", "8001"))
API_BASE = os.getenv("API_BASE", f"http://{BACKEND_HOST}:{BACKEND_PORT}").rstrip("/")
TOKEN = st.session_state.get("token")
HEADERS = {"Accept": "application/json", "Authorization": f"Bearer {TOKEN}"}


def get_events(limit: int, event_type: str | None, agent_key: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {"limit": limit}
    if event_type:
        params["event_type"] = event_type
    if agent_key:
        params["agent_key"] = agent_key
    try:
        response = httpx.get(f"{API_BASE}/observability/events", headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


st.title("🛰️ Activity Timeline")
st.caption("Durable control-plane events. This is the foundation for seeing what Mother AI, agents, and integrations are doing over time.")

left, middle, right = st.columns([1, 1, 1])
with left:
    limit = st.slider("Events", 25, 200, 100, 25)
with middle:
    event_type = st.text_input("Event type", placeholder="e.g. system.ready")
with right:
    agent_key = st.text_input("Agent", placeholder="e.g. crypto")

if st.button("↻ Refresh activity", type="primary"):
    st.rerun()

payload = get_events(limit, event_type.strip() or None, agent_key.strip() or None)
if "error" in payload:
    st.error(payload["error"])
    st.stop()

events = payload.get("events", [])
if not events:
    st.info("No events recorded yet. Start the gateway and perform an operation to populate the timeline.")
    st.stop()

rows = []
for event in events:
    rows.append({
        "Time": event.get("ts"),
        "Agent": event.get("agent_key") or "system",
        "Event": event.get("event_type"),
        "Details": event.get("payload") or {},
        "ID": event.get("id"),
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("Event details")
for event in events:
    label = f"{event.get('ts', '')} · {event.get('agent_key') or 'system'} · {event.get('event_type', '')}"
    with st.expander(label):
        st.json(event.get("payload") or {})
