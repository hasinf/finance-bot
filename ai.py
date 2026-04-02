"""
ai.py — All Claude API interactions:
  1. parse_expense()  → extract description, amount, category from a free-form message
  2. answer_query()   → answer natural language spending questions from DB data
"""

import json
import os
import re
from datetime import date, timedelta

import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-haiku-4-5-20251001"

CATEGORIES = [
    "Food & Drinks",
    "Transport",
    "Entertainment",
    "Shopping",
    "Personal",
    "Bills",
    "Misc",
]

# ---------------------------------------------------------------------------
# 1. Expense parsing
# ---------------------------------------------------------------------------

PARSE_SYSTEM = f"""You are an expense-parsing assistant.
The user sends a short natural-language message describing a purchase.
Extract:
  - description: a clean, concise description of the item/service (no amounts)
  - amount: the numeric amount spent (always a positive number, no currency symbol)
  - category: one of {json.dumps(CATEGORIES)}

Rules:
- The amount may appear anywhere in the sentence (start, middle, or end).
- Words like "spent", "paid", "cost", "for", "on" are hints but not required.
- Choose the most appropriate category based on context, not just keywords.
- If no amount is present, set amount to null.
- Return ONLY a JSON object with keys: description, amount, category.
  No markdown, no explanation, no extra keys.

Examples:
  Input: "coffee at north end 350"
  Output: {{"description":"coffee at north end","amount":350,"category":"Food & Drinks"}}

  Input: "uber ride airport 450"
  Output: {{"description":"uber ride airport","amount":450,"category":"Transport"}}

  Input: "spent 1200 dinner with friends"
  Output: {{"description":"dinner with friends","amount":1200,"category":"Food & Drinks"}}

  Input: "paid 300 for coffee"
  Output: {{"description":"coffee","amount":300,"category":"Food & Drinks"}}
"""


def parse_expense(message: str) -> dict | None:
    """
    Returns dict with keys {description, amount, category}
    or None if the message cannot be understood as an expense.
    """
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=256,
            system=PARSE_SYSTEM,
            messages=[{"role": "user", "content": message}],
        )
        raw = response.content[0].text.strip()
        # Strip accidental markdown fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)

        if data.get("amount") is None:
            return None
        data["amount"] = float(data["amount"])
        return data
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 2. Natural-language query answering
# ---------------------------------------------------------------------------

QUERY_SYSTEM = """You are a personal finance assistant.
The user asks a natural-language question about their expenses.
You will be given:
  - today's date
  - a JSON array of expense records (each has: date, description, amount, category)

Answer the question clearly and concisely.
Format currency values as plain numbers (no symbols unless asked).
Group results logically (by category, by day, etc.) based on the question.
If the data is empty for the requested period, say so politely.
Do NOT invent data. Only use what is provided.
Keep the response short and readable for a Telegram message.
"""


def answer_query(question: str, expenses: list[dict]) -> str:
    today_str = date.today().strftime("%Y-%m-%d (%A)")
    user_content = (
        f"Today's date: {today_str}\n\n"
        f"Expense records:\n{json.dumps(expenses, indent=2)}\n\n"
        f"Question: {question}"
    )
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=QUERY_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Sorry, I couldn't process your query. Error: {e}"


# ---------------------------------------------------------------------------
# 3. Date-range helper (used in bot.py to decide what rows to pass the AI)
# ---------------------------------------------------------------------------

def resolve_date_range(question: str) -> tuple[str, str]:
    """
    Heuristically map common time phrases to (start_date, end_date) strings.
    Falls back to last 30 days for anything unrecognised.
    """
    q = question.lower()
    today = date.today()

    if "today" in q:
        s = e = today
    elif "yesterday" in q:
        s = e = today - timedelta(days=1)
    elif "this week" in q:
        s = today - timedelta(days=today.weekday())  # Monday
        e = today
    elif "last 7 days" in q or "past 7 days" in q:
        s = today - timedelta(days=6)
        e = today
    elif "last 30 days" in q or "past 30 days" in q:
        s = today - timedelta(days=29)
        e = today
    elif "this month" in q:
        s = today.replace(day=1)
        e = today
    elif "last month" in q:
        first_of_this = today.replace(day=1)
        e = first_of_this - timedelta(days=1)
        s = e.replace(day=1)
    else:
        s = today - timedelta(days=29)
        e = today

    return s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")
