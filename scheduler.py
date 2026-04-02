"""
scheduler.py — Sends daily spending summaries at 11 PM (bot's local timezone).
Attach to the running Application via post_init.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import get_all_chat_ids, get_today_summary

logger = logging.getLogger(__name__)


def build_summary_text(summary: dict, total: float) -> str:
    if not summary:
        return "No expenses recorded today. Great job saving! 💰"
    lines = ["📊 *Daily Spending Summary*\n"]
    for category, amount in sorted(summary.items()):
        lines.append(f"• {category}: {amount:,.0f}")
    lines.append(f"\n*Total: {total:,.0f}*")
    return "\n".join(lines)


def start_scheduler(application):
    scheduler = AsyncIOScheduler()

    async def send_summaries():
        chat_ids = get_all_chat_ids()
        for chat_id in chat_ids:
            try:
                summary, total = get_today_summary(chat_id)
                text = build_summary_text(summary, total)
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"Failed to send summary to {chat_id}: {e}")

    # 23:00 every day in the server's local time (UTC on Render; adjust if needed)
    scheduler.add_job(send_summaries, "cron", hour=23, minute=0)
    scheduler.start()
    logger.info("Scheduler started — daily summaries at 23:00 server time.")
