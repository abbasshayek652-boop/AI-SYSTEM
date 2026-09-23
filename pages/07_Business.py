import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Business", page_icon="📊", layout="wide")
token=require_auth(st); st.title("📊 Business")
try: agents=get("/agents",token)
except Exception as exc: st.error(str(exc)); st.stop()
running=[a for a in agents.get("agents",[]) if a.get("running")]; a,b,c=st.columns(3); a.metric("Runtime",agents.get("count",0)); b.metric("Running",len(running)); c.metric("Healthy",agents.get("healthy_count",0))
