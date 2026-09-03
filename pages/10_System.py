from __future__ import annotations

import streamlit as st
from ui.cockpit import get, require_auth

st.set_page_config(page_title="Mother AI · System", page_icon="⚙️", layout="wide")
token = require_auth(st)
st.title("⚙️ System")
st.caption("Control-plane diagnostics, policy catalog, and integration health.")

try:
    health = get("/healthz", token)
    ready = get("/readyz", token)
    integrations = get("/integrations/health", token)
    policies = get("/policy", token)
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))
    st.stop()

left, middle, right = st.columns(3)
left.metric("Gateway", health.get("status", "UNKNOWN"))
middle.metric("Ready", "YES" if ready.get("ready") else "NO")
right.metric("Healthy integrations", f"{integrations.get('healthy_count', 0)}/{integrations.get('count', 0)}")

st.subheader("Integration health")
for item in integrations.get("items", []):
    st.write(f"**{item.get('key')}** · {('HEALTHY' if item.get('healthy') else 'NOT HEALTHY')} · capabilities: {', '.join(item.get('capabilities', []))}")

st.subheader("Capability policy")
st.dataframe(policies.get("items", []), use_container_width=True, hide_index=True)
