from __future__ import annotations

import streamlit as st
from ui.cockpit import get, require_auth

st.set_page_config(page_title="Mother AI · Development", page_icon="💻", layout="wide")
token = require_auth(st)
st.title("💻 Development")
st.caption("Development automation status, with GitHub represented as a safe connection rather than an uncontrolled code executor.")

try:
    connections = get("/observability/connections", token)
    agents = get("/agents", token)
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))
    st.stop()

github = next((x for x in connections.get("items", []) if x.get("key") == "github"), None)
if github:
    a, b = st.columns(2)
    a.metric("GitHub", github.get("status", "UNKNOWN"))
    b.metric("Authenticated", "YES" if github.get("authenticated") else "NO")

for agent in agents.get("agents", []):
    if agent.get("key") in {"github", "testing", "documentation", "debug"}:
        st.write(f"**{agent.get('name', agent.get('key'))}** · {('RUNNING' if agent.get('running') else 'STOPPED')}")
