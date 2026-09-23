import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Connections", page_icon="🔌", layout="wide")
token=require_auth(st); st.title("🔌 Connections"); st.caption("Configuration and live integration health; secrets are never displayed.")
try: config=get("/observability/connections",token); health=get("/integrations/health",token)
except Exception as exc: st.error(str(exc)); st.stop()
for item in config.get("items",[]):
 live=next((x for x in health.get("items",[]) if x.get("key")==item.get("key")),{})
 with st.container(border=True):
  st.subheader(str(item.get("name",item.get("key")))); a,b,c=st.columns(3); a.metric("Configured","YES" if item.get("configured") else "NO"); b.metric("Reachable","YES" if live.get("reachable") else "NO"); c.metric("Authenticated","YES" if live.get("authenticated") else "NO"); st.write(item.get("description",""))
