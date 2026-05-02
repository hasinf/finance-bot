import os
import logging
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health server running on port {port}")
    server.serve_forever()


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
        "/today - Today's expenses\n"
        "/summary - Today's spending summary\n"
        "/help - Show this message"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    expenses = database.get_today_expenses()
    if not expenses:
        await update.message.reply_text("No expenses recorded today.")
        return

    lines = ["*Today's Expenses*\n"]
    total = 0
    for exp in expenses:
        lines.append(f"• {exp['description'].lower()} — {exp['amount']:.0f} ({exp['category']})")
        total += exp["amount"]

    lines.append(f"\n*Total: {total:.0f}*")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    expenses = database.get_today_expenses()
    summary_text = queries.format_daily_summary(expenses)
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


async def main():
    database.init_db()

    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return

    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    if OWNER_ID:
        scheduler.OWNER_CHAT_ID = OWNER_ID
        scheduler.setup_scheduler(app.bot)
        logger.info(f"Daily summary scheduled for user {OWNER_ID}")

    logger.info("Bot started. Polling for updates...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
