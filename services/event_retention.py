from __future__ import annotations

import datetime as dt

from sqlmodel import Session, delete, select

from db.models import AgentEvent
from db.session import engine


def compact_events(*, keep_days: int = 90) -> int:
    """Delete old events; returns the number of removed records."""
    keep_days = max(1, min(keep_days, 3650))
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=keep_days)
    with Session(engine) as session:
        old = session.exec(select(AgentEvent.id).where(AgentEvent.ts < cutoff)).all()
        if not old:
            return 0
        session.exec(delete(AgentEvent).where(AgentEvent.id.in_(old)))
        session.commit()
        return len(old)
