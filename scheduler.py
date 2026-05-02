import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import database
import queries

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

OWNER_CHAT_ID = None


def setup_scheduler(bot):
    scheduler.add_job(
        send_daily_summary,
        CronTrigger(hour=23, minute=0),
        args=[bot],
        id="daily_summary",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info("Daily summary scheduler started (11:00 PM)")


async def send_daily_summary(bot):
    try:
        expenses = database.get_today_expenses()
        summary_text = queries.format_daily_summary(expenses)
        await bot.send_message(chat_id=OWNER_CHAT_ID, text=summary_text, parse_mode="Markdown")
        logger.info("Daily summary sent successfully")
    except Exception as e:
        logger.error(f"Failed to send daily summary: {e}")
