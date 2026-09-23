import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Connections", page_icon="🔌", layout="wide")
token=require_auth(st); st.title("🔌 Connections"); st.caption("Configuration and live integration health; secrets are never displayed.")
try:
 c=get("/observability/connections",token); h=get("/integrations/health",token)
except Exception as exc: st.error(str(exc)); st.stop()
for x in c.get("items",[]):
 y=next((z for z in h.get("items",[]) if z.get("key")==x.get("key")),{})
 with st.container(border=True):
  st.subheader(str(x.get("name",x.get("key")))); a,b,cx=st.columns(3); a.metric("Configured","YES" if x.get("configured") else "NO"); b.metric("Reachable","YES" if y.get("reachable") else "NO"); cx.metric("Authenticated","YES" if y.get("authenticated") else "NO"); st.write(x.get("description",""))