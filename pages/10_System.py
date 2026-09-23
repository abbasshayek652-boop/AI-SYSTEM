import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · System", page_icon="⚙️", layout="wide")
token=require_auth(st); st.title("⚙️ System")
try: health=get("/healthz",token); ready=get("/readyz",token); status=get("/status",token); catalog=get("/catalog",token)
except Exception as exc: st.error(str(exc)); st.stop()
a,b,c,d=st.columns(4); a.metric("Gateway","ONLINE"); b.metric("Ready","YES" if ready.get("ready") else "NO"); c.metric("API",health.get("api_version","unknown")); d.metric("Catalog",catalog.get("count",0)); st.json(status)
