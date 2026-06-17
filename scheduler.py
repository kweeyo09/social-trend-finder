"""
scheduler.py
Runs the trend report on a schedule using APScheduler.
Default: Mon / Wed / Fri at 08:00 in configured timezone.

Start with: python scheduler.py
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from main import run_trend_report
import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone=settings.TIMEZONE)

scheduler.add_job(
    run_trend_report,
    CronTrigger(
        day_of_week="mon,wed,fri",
        hour=8,
        minute=0,
        timezone=settings.TIMEZONE,
    ),
    id="trend_report",
    name="Social Trend Finder",
    replace_existing=True,
)

if __name__ == "__main__":
    logger.info(
        f"Scheduler started. Trend reports will run Mon/Wed/Fri at 08:00 {settings.TIMEZONE}."
    )
    logger.info("Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
