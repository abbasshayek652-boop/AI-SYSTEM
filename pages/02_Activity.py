import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Activity", page_icon="🧾", layout="wide")
token=require_auth(st); st.title("🧾 Activity")
limit=st.slider("Events",20,200,50,10)
try: p=get("/observability/events",token,limit=limit)
except Exception as exc: st.error(str(exc)); st.stop()
for e in p.get("events",[]):
 with st.container(border=True): st.write(str(e.get("ts"))+" · "+str(e.get("event_type"))); st.json(e.get("payload") or {})