from __future__ import annotations

import uuid
from typing import Any

from services.event_store import record_event


EVENT_CATEGORIES = frozenset({"system", "agent", "integration", "decision", "approval", "action", "error"})


def emit(
    event_type: str,
    *,
    category: str,
    source: str,
    agent_key: str | None = None,
    correlation_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> str:
    if category not in EVENT_CATEGORIES:
        raise ValueError(f"Unsupported event category: {category}")
    cid = correlation_id or str(uuid.uuid4())
    data = dict(payload or {})
    data["_meta"] = {"category": category, "source": source, "correlation_id": cid, "schema_version": "1.0"}
    record_event(event_type, agent_key=agent_key, payload=data)
    return cid
