from __future__ import annotations

import streamlit as st
from ui.cockpit import get, require_auth

st.set_page_config(page_title="Mother AI · Content", page_icon="📣", layout="wide")
token = require_auth(st)
st.title("📣 Content")
st.caption("Content drafts and publishing approvals. Publishing remains explicitly gated.")

try:
    approvals = get("/approvals", token)
    events = get("/observability/events", token, limit=100)
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))
    st.stop()

pending = [x for x in approvals.get("items", []) if x.get("target") == "linkedin"]
a, b = st.columns(2)
a.metric("Pending LinkedIn approvals", len(pending))
b.metric("Publishing policy", "APPROVAL REQUIRED")

st.subheader("Recent content activity")
for event in events.get("events", []):
    if event.get("event_type", "").startswith(("approval.", "content.")):
        st.write(f"`{event.get('ts')}` · `{event.get('event_type')}` · `{event.get('agent_key') or 'system'}`")
