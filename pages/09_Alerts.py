from __future__ import annotations

import streamlit as st
from ui.cockpit import get, require_auth

st.set_page_config(page_title="Mother AI · Alerts", page_icon="🚨", layout="wide")
token = require_auth(st)
st.title("🚨 Alerts")
st.caption("Failures and degraded integrations are surfaced from the durable event stream.")

try:
    events = get("/observability/events", token, limit=200)
    status = get("/status", token)
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))
    st.stop()

circuit = status.get("circuit_breaker", {})
if circuit.get("open"):
    st.error(f"Control circuit open: {circuit.get('reason') or 'unknown reason'}")
else:
    st.success("Control circuit closed.")

errors = [e for e in events.get("events", []) if str(e.get("event_type", "")).endswith(("error", "failed")) or str(e.get("event_type", "")).startswith("error.")]
st.metric("Recent error events", len(errors))
for event in errors:
    st.write(f"`{event.get('ts')}` · `{event.get('event_type')}` · `{event.get('agent_key') or 'system'}`")
