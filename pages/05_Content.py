import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Content", page_icon="✍️", layout="wide")
token=require_auth(st); st.title("✍️ Content"); st.caption("Publishing remains approval-gated.")
try: connections=get("/observability/connections",token); events=get("/observability/events",token,limit=50)
except Exception as exc: st.error(str(exc)); st.stop()
li=next((x for x in connections.get("items",[]) if x.get("key")=="linkedin"),{}); st.metric("LinkedIn","CONFIGURED" if li.get("configured") else "NOT CONFIGURED")
for e in events.get("events",[]):
 if "linkedin" in str(e.get("event_type","")) or "content" in str(e.get("event_type","")): st.write(str(e.get("ts"))+" · "+str(e.get("event_type")))
