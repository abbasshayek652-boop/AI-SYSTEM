from __future__ import annotations

import streamlit as st
from ui.cockpit import get, require_auth

token = require_auth(st)
st.title("💰 Finance")
st.caption("Unified finance view. Account data is read-only; consequential financial actions remain disabled.")

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

if binance and binance.get("authenticated"):
    if st.button("Refresh Binance balances"):
        try:
            snapshot = get("/integrations/binance/balances", token)
            balances = snapshot.get("balances", [])
            if balances:
                st.dataframe(balances, use_container_width=True, hide_index=True)
            else:
                st.info("No non-zero balances returned.")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
else:
    st.info("Configure the Binance read-only adapter to view balances.")

st.subheader("Recent crypto-agent activity")
for event in events.get("events", []):
    st.write(f"`{event.get('ts')}` · `{event.get('event_type')}`")
