import re
from datetime import date, timedelta
from collections import defaultdict
import database


def parse_timeframe(text: str) -> tuple[date, date, str] | None:
    text_lower = text.lower()
    today = date.today()

    if "today" in text_lower:
        return (today, today, "Today")

    if "yesterday" in text_lower:
        yesterday = today - timedelta(days=1)
        return (yesterday, yesterday, "Yesterday")

    last_7 = re.search(r'(?:last\s+)?7\s*(?:days?|d)', text_lower)
    if last_7:
        start = today - timedelta(days=6)
        return (start, today, "Last 7 Days")

    last_30 = re.search(r'(?:last\s+)?30\s*(?:days?|d)', text_lower)
    if last_30:
        start = today - timedelta(days=29)
        return (start, today, "Last 30 Days")

    this_week = re.search(r'this\s+week', text_lower)
    if this_week:
        start = today - timedelta(days=today.weekday())
        return (start, today, "This Week")

    last_week = re.search(r'last\s+week', text_lower)
    if last_week:
        start = today - timedelta(days=today.weekday() + 7)
        end = today - timedelta(days=today.weekday() + 1)
        return (start, end, "Last Week")

    this_month = re.search(r'this\s+month', text_lower)
    if this_month:
        start = today.replace(day=1)
        return (start, today, "This Month")

    last_month = re.search(r'last\s+month', text_lower)
    if last_month:
        if today.month == 1:
            start = today.replace(year=today.year - 1, month=12, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            start = today.replace(month=today.month - 1, day=1)
            end = today.replace(day=1) - timedelta(days=1)
        return (start, end, "Last Month")

    last_365 = re.search(r'(?:last\s+)?(?:year|365\s*days?)', text_lower)
    if last_365:
        start = today - timedelta(days=364)
        return (start, today, "Last Year")

    return None


def parse_category_query(text: str) -> str | None:
    text_lower = text.lower()
    categories = database.get_all_categories()

    category_map = {}
    for cat in categories:
        category_map[cat.lower()] = cat

    short_map = {
        "food": "Food & Drinks",
        "drink": "Food & Drinks",
        "drinks": "Food & Drinks",
        "transport": "Transport",
        "transit": "Transport",
        "commute": "Transport",
        "entertainment": "Entertainment",
        "fun": "Entertainment",
        "shopping": "Shopping",
        "shop": "Shopping",
        "personal": "Personal",
        "health": "Personal",
        "bills": "Bills",
        "bill": "Bills",
        "utilities": "Bills",
        "utility": "Bills",
        "misc": "Misc",
        "other": "Misc",
    }

    for short, full in short_map.items():
        if short in text_lower and full in categories:
            return full

    for cat_lower, cat_full in category_map.items():
        if cat_lower in text_lower:
            return cat_full

    return None


def handle_query(text: str) -> str | None:
    text_lower = text.lower()

    query_words = [
        "how much", "spend", "spent", "expenses", "expense",
        "total", "summary", "show", "what", "spending",
    ]
    is_query = any(word in text_lower for word in query_words)

    bare_time = [
        "today", "yesterday", "this week", "last week",
        "this month", "last month", "last 7", "last 30",
    ]
    is_bare_time = any(b in text_lower for b in bare_time)

    if not is_query and not is_bare_time:
        return None

    timeframe = parse_timeframe(text_lower)
    if not timeframe:
        return "I couldn't understand the time period. Try: today, yesterday, this week, last 7 days, this month, etc."

    start, end, timeframe_label = timeframe

    category = parse_category_query(text_lower)

    if category:
        expenses = database.get_expenses_by_category_and_range(category, start, end)
        return format_query_response(expenses, timeframe_label, category)
    else:
        expenses = database.get_expenses_by_date_range(start, end)
        return format_query_response(expenses, timeframe_label)


def format_query_response(expenses: list[dict], timeframe_label: str, category: str | None = None) -> str:
    if not expenses:
        label = f"{category} " if category else ""
        return f"No {label.lower()}expenses found for {timeframe_label}."

    if timeframe_label == "Today" and not category:
        lines = ["*Today's Expenses*\n"]
        total = 0
        for exp in expenses:
            lines.append(f"• {exp['description'].lower()} — {exp['amount']:.0f} ({exp['category']})")
            total += exp["amount"]
        lines.append(f"\n*Total: {total:.0f}*")
        return "\n".join(lines)

    if category:
        by_date = defaultdict(float)
        for exp in expenses:
            by_date[exp["date"]] += exp["amount"]

        lines = [f"*{category} ({timeframe_label})*\n"]
        total = 0
        for d in sorted(by_date.keys()):
            amount = by_date[d]
            total += amount
            date_obj = date.fromisoformat(d)
            day_name = date_obj.strftime("%A")
            lines.append(f"{day_name}: {amount:.0f}")

        lines.append(f"\n*Total: {total:.0f}*")
        return "\n".join(lines)
    else:
        by_category = defaultdict(float)
        for exp in expenses:
            by_category[exp["category"]] += exp["amount"]

        lines = [f"*Spending Summary ({timeframe_label})*\n"]
        total = 0
        for cat in sorted(by_category.keys()):
            amount = by_category[cat]
            total += amount
            lines.append(f"{cat}: {amount:.0f}")

        lines.append(f"\n*Total: {total:.0f}*")
        return "\n".join(lines)


def format_daily_summary(expenses: list[dict]) -> str:
    if not expenses:
        return "No expenses recorded today."

    by_category = defaultdict(float)
    for exp in expenses:
        by_category[exp["category"]] += exp["amount"]

    lines = ["*Daily Spending Summary*\n"]
    total = 0
    for category in sorted(by_category.keys()):
        amount = by_category[category]
        total += amount
        lines.append(f"{category}: {amount:.0f}")

    lines.append(f"\n*Total: {total:.0f}*")
    return "\n".join(lines)
