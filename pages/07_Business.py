from __future__ import annotations

import streamlit as st
from ui.cockpit import get, require_auth

st.set_page_config(page_title="Mother AI · Business", page_icon="💼", layout="wide")
token = require_auth(st)
st.title("💼 Business")
st.caption("Business capabilities are shown from the same runtime catalog and event stream; no client-facing automation is enabled by default.")

try:
    catalog = get("/catalog", token)
    events = get("/observability/events", token, limit=100)
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))
    st.stop()

items = [a for a in catalog.get("agents", []) if str(a.get("layer", "")).lower() == "business"]
st.metric("Business capabilities", len(items))
for item in items:
    runtime = item.get("runtime", {})
    st.write(f"**{item.get('name')}** · `{item.get('key')}` · {('LOADED' if runtime.get('loaded') else 'CATALOG')}")

st.subheader("Recent business-related events")
for event in events.get("events", []):
    if event.get("event_type", "").startswith("business."):
        st.write(f"`{event.get('ts')}` · `{event.get('event_type')}`")
