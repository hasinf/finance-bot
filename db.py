import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.environ.get("DB_PATH", "expenses.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id   TEXT    NOT NULL,
                date      TEXT    NOT NULL,
                time      TEXT    NOT NULL,
                description TEXT  NOT NULL,
                amount    REAL    NOT NULL,
                category  TEXT    NOT NULL
            )
        """)
        conn.commit()


def save_expense(chat_id: str, description: str, amount: float, category: str):
    now = datetime.now()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO expenses (chat_id, date, time, description, amount, category)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (chat_id, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
             description, amount, category),
        )
        conn.commit()


def get_expenses(chat_id: str, start_date: str, end_date: str = None):
    """Return expenses for a chat between start_date and end_date (inclusive)."""
    if end_date is None:
        end_date = start_date
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM expenses
               WHERE chat_id = ? AND date >= ? AND date <= ?
               ORDER BY date, time""",
            (chat_id, start_date, end_date),
        ).fetchall()
    return [dict(r) for r in rows]


def get_today_summary(chat_id: str):
    today = date.today().strftime("%Y-%m-%d")
    rows = get_expenses(chat_id, today)
    summary = {}
    for r in rows:
        summary.setdefault(r["category"], 0)
        summary[r["category"]] += r["amount"]
    return summary, sum(summary.values())


def get_all_chat_ids():
    """Return distinct chat_ids that have at least one expense today."""
    today = date.today().strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT chat_id FROM expenses WHERE date = ?", (today,)
        ).fetchall()
    return [r["chat_id"] for r in rows]
