import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Intelligence", page_icon="🧠", layout="wide")
token=require_auth(st); st.title("🧠 Intelligence")
try: executive=get("/executive/status",token); events=get("/observability/events",token,limit=50)
except Exception as exc: st.error(str(exc)); st.stop()
st.json(executive)
for e in events.get("events",[]):
 if str(e.get("event_type","")).startswith(("system.","executive.","learning.")): st.write(str(e.get("ts"))+" · "+str(e.get("event_type")))
