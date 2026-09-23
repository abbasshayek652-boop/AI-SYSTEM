import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Alerts", page_icon="🚨", layout="wide")
token=require_auth(st); st.title("🚨 Alerts")
try: events=get("/observability/events",token,limit=100)
except Exception as exc: st.error(str(exc)); st.stop()
alerts=[e for e in events.get("events",[]) if any(k in str(e.get("event_type","")).lower() for k in ("failed","error","alert","warning"))]
if not alerts: st.success("No recent alert/error events found.")
for e in alerts: st.error(str(e.get("ts"))+" · "+str(e.get("event_type"))); st.json(e.get("payload") or {})
