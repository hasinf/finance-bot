import os
import libsql
from datetime import datetime, date, timedelta

TURSO_URL = os.environ.get("TURSO_DB_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
TZ_OFFSET = int(os.environ.get("TIMEZONE_OFFSET", 0))

def _local_now() -> datetime:
    return datetime.utcnow() + timedelta(hours=TZ_OFFSET)

def _local_today() -> str:
    return _local_now().strftime("%Y-%m-%d")

def get_connection():
    if TURSO_URL and TURSO_TOKEN:
        return libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)
    else:
        return libsql.connect("file:expenses.db")

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
    now = _local_now()
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
    today = _local_today()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE date = ? ORDER BY time", (today,)
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "date": r[1], "time": r[2], "description": r[3], "amount": r[4], "category": r[5]}
        for r in rows
    ]

def get_expenses_by_date_range(start: date, end: date) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date, time",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "date": r[1], "time": r[2], "description": r[3], "amount": r[4], "category": r[5]}
        for r in rows
    ]

def get_expenses_by_category_and_range(category: str, start: date, end: date) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE category = ? AND date BETWEEN ? AND ? ORDER BY date, time",
        (category, start.isoformat(), end.isoformat()),
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "date": r[1], "time": r[2], "description": r[3], "amount": r[4], "category": r[5]}
        for r in rows
    ]

def get_all_categories() -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT category FROM expenses ORDER BY category"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]
