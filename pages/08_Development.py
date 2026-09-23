import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Development", page_icon="🛠️", layout="wide")
token=require_auth(st); st.title("🛠️ Development"); st.caption("Development controls do not modify production source automatically.")
try: agents=get("/agents",token); policies=get("/policy",token)
except Exception as exc: st.error(str(exc)); st.stop()
for x in agents.get("agents",[]):
 if x.get("key") in {"github","testing","documentation","development"}: st.write(str(x.get("name",x.get("key")))+" — "+("running" if x.get("running") else "stopped"))
st.subheader("Policy boundary"); st.json(policies)
