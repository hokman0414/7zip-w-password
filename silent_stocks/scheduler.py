"""Daily scheduler: runs the research pipeline at 09:00 America/New_York on weekdays (configurable)."""
from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Settings
from .daily import run_daily

log = logging.getLogger(__name__)


def build_trigger(settings: Settings) -> CronTrigger:
    return CronTrigger(day_of_week="mon-fri", hour=settings.daily_run_hour, minute=0, timezone=settings.timezone)


def _job(settings: Settings) -> None:
    try:
        res = run_daily(settings)
        log.info("daily run %s complete: %d reports, %d alerts, brief %s", res["run_id"], len(res["reports"]),
                 len(res["alerts"]), res["brief"])
    except Exception:  # noqa: BLE001 - a failed day must not kill the scheduler
        log.exception("daily run failed")


def serve(settings: Settings) -> None:
    sched = BlockingScheduler(timezone=settings.timezone)
    sched.add_job(_job, build_trigger(settings), args=[settings], id="silent-stocks-daily", coalesce=True,
                  misfire_grace_time=3600, max_instances=1)
    log.info("scheduled: weekdays %02d:00 %s", settings.daily_run_hour, settings.timezone)
    sched.start()
