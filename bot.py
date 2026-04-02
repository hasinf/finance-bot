"""
bot.py — Entry point for the Telegram expense tracker bot.

Flow for each incoming message:
  1. Is it a /command? → handle directly.
  2. Does it look like a natural-language query?  → answer_query path.
  3. Otherwise → parse_expense path → save → confirm.
"""

import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import db
import ai
from scheduler import start_scheduler

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword sets used to decide if a message is a QUERY vs. a new expense log
# ---------------------------------------------------------------------------
QUERY_KEYWORDS = {
    "how much", "total", "spent", "expenses", "spending",
    "last 7 days", "this week", "this month", "yesterday",
    "today", "last month", "past", "summary", "show",
}

def looks_like_query(text: str) -> bool:
    lower = text.lower()
    # If the message contains a query keyword AND does NOT contain a bare amount
    # immediately (i.e. it reads like a question rather than "coffee 300")
    has_keyword = any(kw in lower for kw in QUERY_KEYWORDS)
    # A standalone number at the END strongly suggests an expense log
    import re
    ends_with_number = bool(re.search(r"\b\d+(\.\d+)?\s*$", text.strip()))
    # Starts with a question-style keyword with no trailing amount → likely a query
    if has_keyword and not ends_with_number:
        return True
    # Also treat messages longer than ~8 words without a number as queries
    words = lower.split()
    import re as _re
    has_any_number = bool(_re.search(r"\d", text))
    if len(words) > 6 and not has_any_number:
        return True
    return False


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your personal finance tracker.\n\n"
        "Just tell me what you spent, like:\n"
        "  • coffee at north end 350\n"
        "  • uber ride airport 450\n"
        "  • spent 1200 dinner with friends\n\n"
        "You can also ask me questions like:\n"
        "  • food expenses last 7 days\n"
        "  • how much did I spend this week\n"
        "  • transport expenses today\n\n"
        "I'll send you a daily summary at 11 PM. Let's start! 💰"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*How to use this bot:*\n\n"
        "*Log an expense:*\n"
        "  coffee 300\n"
        "  uber ride 450\n"
        "  paid 1200 for dinner\n"
        "  croissant and latte 420\n\n"
        "*Ask a question:*\n"
        "  food expenses last 7 days\n"
        "  how much did I spend this week\n"
        "  transport expenses today\n"
        "  total expenses this month\n\n"
        "*Commands:*\n"
        "  /start — welcome message\n"
        "  /help  — this message\n"
        "  /today — today's spending summary\n",
        parse_mode="Markdown",
    )


async def today_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    from scheduler import build_summary_text
    summary, total = db.get_today_summary(chat_id)
    text = build_summary_text(summary, total)
    await update.message.reply_text(text, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Main message handler
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)

    if not text:
        return

    # --- QUERY PATH ---
    if looks_like_query(text):
        start_date, end_date = ai.resolve_date_range(text)
        expenses = db.get_expenses(chat_id, start_date, end_date)
        answer = ai.answer_query(text, expenses)
        await update.message.reply_text(answer)
        return

    # --- EXPENSE LOGGING PATH ---
    parsed = ai.parse_expense(text)

    if parsed is None:
        await update.message.reply_text(
            "🤔 I couldn't understand that expense. "
            "Could you make sure to include the amount?\n\n"
            "Example: *coffee 350* or *uber ride 450*",
            parse_mode="Markdown",
        )
        return

    description = parsed["description"]
    amount = parsed["amount"]
    category = parsed["category"]

    db.save_expense(chat_id, description, amount, category)

    await update.message.reply_text(
        f"✅ Saved: *{description}* — {amount:,.0f} _({category})_",
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main():
    db.init_db()

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today_summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the daily summary scheduler
    start_scheduler(app)

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
