from __future__ import annotations

import datetime as dt
from typing import Any

from sqlmodel import Session, select

from db.models import AgentEvent
from db.session import engine


def record_event(
    event_type: str,
    *,
    agent_key: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AgentEvent:
    event = AgentEvent(
        ts=dt.datetime.utcnow(),
        agent_key=agent_key,
        event_type=event_type,
        payload=payload or {},
    )
    with Session(engine) as session:
        session.add(event)
        session.commit()
        session.refresh(event)
    return event


def recent_events(
    *,
    limit: int = 100,
    event_type: str | None = None,
    agent_key: str | None = None,
) -> list[AgentEvent]:
    limit = max(1, min(limit, 500))
    with Session(engine) as session:
        statement = select(AgentEvent)
        if event_type:
            statement = statement.where(AgentEvent.event_type == event_type)
        if agent_key:
            statement = statement.where(AgentEvent.agent_key == agent_key)
        statement = statement.order_by(AgentEvent.ts.desc()).limit(limit)
        return list(session.exec(statement).all())
