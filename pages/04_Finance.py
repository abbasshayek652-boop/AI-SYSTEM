import streamlit as st
from ui.cockpit import get, require_auth
st.set_page_config(page_title="Mother AI · Finance", page_icon="💰", layout="wide")
token=require_auth(st); st.title("💰 Finance"); st.caption("Binance is read-only; no trading execution is exposed.")
try: health=get("/integrations/health",token)
except Exception as exc: st.error(str(exc)); st.stop()
b=next((x for x in health.get("items",[]) if x.get("key")=="binance"),{}); a,c=st.columns(2); a.metric("Configured","YES" if b.get("configured") else "NO"); c.metric("Mode","READ ONLY")
if b.get("configured") and b.get("authenticated") and st.button("Refresh balances"):
 try: st.dataframe(get("/integrations/binance/balances",token).get("balances",[]),use_container_width=True,hide_index=True)
 except Exception as exc: st.error(str(exc))
else: st.info("Configure Binance credentials for a read-only balance snapshot.")
