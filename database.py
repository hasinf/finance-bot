import sqlite3
import os
from datetime import datetime, date, timedelta
from typing import Optional


DB_PATH = os.environ.get("DB_PATH", "expenses.db")


def get_connection() -> sqlite3.Connection:
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_expense(description: str, amount: float, category: str) -> dict:
    now = datetime.now()
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO expenses (date, time, description, amount, category) VALUES (?, ?, ?, ?, ?)",
        (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), description, amount, category),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return {
        "id": expense_id,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "description": description,
        "amount": amount,
        "category": category,
    }


def get_today_expenses() -> list[dict]:
    today = date.today().isoformat()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE date = ? ORDER BY time", (today,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_expenses_by_date_range(start: date, end: date) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date, time",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_expenses_by_category_and_range(category: str, start: date, end: date) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE category = ? AND date BETWEEN ? AND ? ORDER BY date, time",
        (category, start.isoformat(), end.isoformat()),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_categories() -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT category FROM expenses ORDER BY category"
    ).fetchall()
    conn.close()
    return [row["category"] for row in rows]
