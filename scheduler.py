import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import database
import telegram


logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler(bot: telegram.Bot, chat_id: int):
    scheduler.add_job(
        send_daily_summary,
        CronTrigger(hour=23, minute=0),
        args=[bot, chat_id],
        id="daily_summary",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Daily summary scheduler started (11:00 PM)")


async def send_daily_summary(bot: telegram.Bot, chat_id: int):
    try:
        expenses = database.get_today_expenses()
        summary = _format_summary(expenses)
        await bot.send_message(chat_id=chat_id, text=summary, parse_mode="Markdown")
        logger.info("Daily summary sent successfully")
    except Exception as e:
        logger.error(f"Failed to send daily summary: {e}")


def _format_summary(expenses: list[dict]) -> str:
    if not expenses:
        return "*Daily Spending Summary*\n\nNo expenses recorded today."

    by_category = {}
    for exp in expenses:
        cat = exp["category"]
        by_category[cat] = by_category.get(cat, 0) + exp["amount"]

    lines = ["*Daily Spending Summary*\n"]
    total = 0
    for category in sorted(by_category.keys()):
        amount = by_category[category]
        total += amount
        lines.append(f"{category}: {amount:.0f}")

    lines.append(f"\n*Total: {total:.0f}*")
    return "\n".join(lines)
