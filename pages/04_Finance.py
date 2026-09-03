from __future__ import annotations

import streamlit as st
from ui.cockpit import get, require_auth

st.set_page_config(page_title="Mother AI · Finance", page_icon="💰", layout="wide")
token = require_auth(st)
st.title("💰 Finance")
st.caption("Unified finance view. Real balances appear only when a supported account adapter is configured.")

try:
    connections = get("/observability/connections", token)
    events = get("/observability/events", token, limit=100, agent_key="crypto")
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))
    st.stop()

binance = next((x for x in connections.get("items", []) if x.get("key") == "binance"), None)
if binance:
    a, b, c = st.columns(3)
    a.metric("Binance", binance.get("status", "UNKNOWN"))
    b.metric("Authenticated", "YES" if binance.get("authenticated") else "NO")
    c.metric("Mode", "READ ONLY")

st.subheader("Recent crypto-agent activity")
for event in events.get("events", []):
    st.write(f"`{event.get('ts')}` · `{event.get('event_type')}`")
