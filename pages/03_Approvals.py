from __future__ import annotations

from typing import Any

import os
import httpx
import streamlit as st

st.set_page_config(page_title="Mother AI · Approvals", page_icon="✅", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Sign in from the Mother AI home page first.")
    st.stop()

base = os.getenv("API_BASE", f"http://{os.getenv('MOTHER_BACKEND_HOST', '127.0.0.1')}:{os.getenv('MOTHER_BACKEND_PORT', '8001')}").rstrip("/")
headers = {"Accept": "application/json", "Authorization": f"Bearer {st.session_state.get('token')}"}


def get_pending() -> dict[str, Any]:
    response = httpx.get(f"{base}/approvals", headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def decide(approval_id: int, approved: bool, note: str) -> dict[str, Any]:
    response = httpx.post(f"{base}/approvals/{approval_id}/decision", headers=headers, json={"approved": approved, "note": note or None}, timeout=10)
    response.raise_for_status()
    return response.json()

st.title("✅ Approvals")
st.caption("Consequential actions must pass through an explicit policy boundary. Approval here does not itself execute an external action; it records the operator decision for the workflow engine.")

try:
    payload = get_pending()
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))
    st.stop()

items = payload.get("items", [])
st.metric("Pending approvals", len(items))

if not items:
    st.success("Nothing is waiting for approval.")
else:
    for item in items:
        with st.container(border=True):
            st.subheader(f"#{item['id']} · {item['capability']}")
            st.write(f"**Target:** {item['target']}")
            st.write(f"**Requested by:** {item['requested_by']}")
            if item.get("reason"):
                st.write(f"**Reason:** {item['reason']}")
            with st.expander("Payload"):
                st.json(item.get("payload") or {})
            note = st.text_input("Decision note", key=f"note_{item['id']}")
            left, right = st.columns(2)
            with left:
                if st.button("Approve", key=f"approve_{item['id']}", type="primary", use_container_width=True):
                    try:
                        decide(int(item["id"]), True, note)
                        st.success("Approval recorded.")
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        st.error(str(exc))
            with right:
                if st.button("Reject", key=f"reject_{item['id']}", use_container_width=True):
                    try:
                        decide(int(item["id"]), False, note)
                        st.warning("Rejection recorded.")
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        st.error(str(exc))
