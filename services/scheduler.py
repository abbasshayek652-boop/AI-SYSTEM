from __future__ import annotations

import datetime as dt
import logging
from typing import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

StatusProvider = Callable[[], Awaitable[dict[str, object]]]
Notifier = Callable[[str, dict[str, object]], Awaitable[None]]
LOGGER = logging.getLogger("scheduler")


class ControlScheduler:
    """Application scheduler for periodic self-checks and summaries."""

    def __init__(self, status_provider: StatusProvider, notifier: Notifier) -> None:
        self._status_provider = status_provider
        self._notifier = notifier
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._started = False

    @property
    def running(self) -> bool:
        return self._started

    def start(self) -> None:
        if self._started:
            return
        self._scheduler.add_job(self._self_check, "interval", minutes=5, id="mother-self-check", replace_existing=True, coalesce=True, max_instances=1)
        self._scheduler.add_job(self._daily_summary, "cron", hour=0, minute=5, id="mother-daily-summary", replace_existing=True, coalesce=True, max_instances=1)
        self._scheduler.add_job(self._weekly_compaction, "cron", day_of_week="mon", hour=0, minute=15, id="mother-weekly-audit", replace_existing=True, coalesce=True, max_instances=1)
        self._scheduler.start()
        self._started = True
        LOGGER.info("Control scheduler started")

    async def stop(self) -> None:
        if not self._started:
            return
        try:
            self._scheduler.shutdown(wait=False)
        except RuntimeError as exc:
            # APScheduler retains the loop it was started on. Tests and embedded
            # runners may close that loop before shutdown is invoked.
            if "Event loop is closed" not in str(exc):
                raise
        finally:
            self._started = False
        LOGGER.info("Control scheduler stopped")

    async def _daily_summary(self) -> None:
        try:
            payload = await self._status_provider()
            await self._notifier("daily_summary", payload)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Daily summary failed")

    async def _weekly_compaction(self) -> None:
        try:
            payload = {"event": "audit_compaction", "ts": dt.datetime.now(dt.timezone.utc).isoformat()}
            await self._notifier("weekly_audit", payload)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Weekly audit event failed")

    async def _self_check(self) -> None:
        try:
            payload = await self._status_provider()
            await self._notifier("self_check", payload)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Scheduler self-check failed")


async def send_telegram_summary(kind: str, payload: dict[str, object]) -> None:
    LOGGER.info("scheduler event", extra={"kind": kind, "payload": payload})


def build_scheduler(status_provider: StatusProvider, notifier: Notifier | None = None) -> ControlScheduler:
    return ControlScheduler(status_provider, notifier or send_telegram_summary)
