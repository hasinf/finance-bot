import os
import logging
import telegram
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import database
import expense_parser
import categorizer
import queries
import scheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.environ.get("TELEGRAM_OWNER_ID", 0))

AUTHORIZED_USERS = set()
if OWNER_ID:
    AUTHORIZED_USERS.add(OWNER_ID)

extra_ids = os.environ.get("AUTHORIZED_USER_IDS", "")
if extra_ids:
    for uid in extra_ids.split(","):
        uid = uid.strip()
        if uid.isdigit():
            AUTHORIZED_USERS.add(int(uid))


def is_authorized(user_id: int) -> bool:
    if not AUTHORIZED_USERS:
        return True
    return user_id in AUTHORIZED_USERS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    welcome = (
        "*Expense Tracker Bot*\n\n"
        "Send expenses naturally:\n"
        "_coffee at north end 350_\n"
        "_uber ride airport 450_\n"
        "_spent 1200 dinner with friends_\n\n"
        "Ask about expenses:\n"
        "_food expenses this week_\n"
        "_how much did i spend this month_\n"
        "_transport expenses today_\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/summary - Today's spending summary\n"
        "/help - Show this message"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    expenses = database.get_today_expenses()
    summary_text = scheduler._format_summary(expenses)
    await update.message.reply_text(summary_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    text = update.message.text.strip()

    query_response = queries.handle_query(text)
    if query_response:
        await update.message.reply_text(query_response, parse_mode="Markdown")
        return

    amount = expense_parser.extract_amount(text)
    if amount is None:
        await update.message.reply_text(
            "I couldn't understand the expense. Could you include the amount?\n\n"
            "Examples:\n"
            "_coffee 300_\n"
            "_spent 350 on lunch_\n"
            "_uber ride 450_"
        )
        return

    description = expense_parser.extract_description(text, amount)
    category = categorizer.detect_category(text)

    expense = database.add_expense(description, amount, category)

    confirmation = (
        f"Saved: {expense['description'].lower()} - "
        f"{expense['amount']:.0f} ({expense['category']})"
    )
    await update.message.reply_text(confirmation)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Something went wrong. Please try again."
        )


def main():
    database.init_db()

    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    if OWNER_ID:
        bot_instance = app.bot
        scheduler.setup_scheduler(bot_instance, OWNER_ID)
        logger.info(f"Daily summary scheduled for user {OWNER_ID}")

    logger.info("Bot started. Polling for updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
