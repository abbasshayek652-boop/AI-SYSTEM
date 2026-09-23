from __future__ import annotations

import streamlit as st
from ui.cockpit import get, require_auth

st.set_page_config(page_title="Mother AI · Intelligence", page_icon="📰", layout="wide")
token = require_auth(st)
st.title("📰 Intelligence")
st.caption("A read-only operational view for intelligence agents and their event stream.")

try:
    agents = get("/agents", token)
    events = get("/observability/events", token, limit=100)
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))
    st.stop()

intelligence = [a for a in agents.get("agents", []) if str(a.get("layer", "")).lower() in {"intelligence", "learning"} or a.get("key") in {"news", "sentiment", "economic", "competitor", "learning"}]
st.metric("Intelligence / learning runtime agents", len(intelligence))
for agent in intelligence:
    st.write(f"**{agent.get('name', agent.get('key'))}** · {('RUNNING' if agent.get('running') else 'STOPPED')}")

st.subheader("Recent intelligence events")
for event in events.get("events", []):
    if event.get("agent_key") in {a.get("key") for a in intelligence}:
        st.write(f"`{event.get('ts')}` · `{event.get('event_type')}`")
