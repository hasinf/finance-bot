import re


def extract_amount(text: str) -> float | None:
    patterns = [
        r'(?:spent|paid|cost|price)\s+(?:\$|€|£)?\s*(\d+(?:[.,]\d+)?)',
        r'(?:\$|€|£)\s*(\d+(?:[.,]\d+)?)',
        r'(\d+(?:[.,]\d+)?)\s*(?:dollars?|usd|eur|gbp|tk|bdt|rupees?)',
        r'(\d+(?:[.,]\d+)?)\s*$',
        r'\s(\d+(?:[.,]\d+)?)\s*$',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", ".")
            return float(amount_str)

    match = re.search(r'(\d+(?:[.,]\d+)?)', text)
    if match:
        amount_str = match.group(1).replace(",", ".")
        amount = float(amount_str)
        if 1 <= amount <= 999999:
            return amount

    return None


def extract_description(text: str, amount: float) -> str:
    amount_str = str(amount)
    if amount == int(amount):
        amount_str = str(int(amount))

    description = text
    description = re.sub(
        r'(?:spent|paid|cost|price)\s+(?:\$|€|£)?\s*' + re.escape(amount_str),
        "", description, flags=re.IGNORECASE
    )
    description = re.sub(
        r'(?:\$|€|£)\s*' + re.escape(amount_str),
        "", description, flags=re.IGNORECASE
    )
    description = re.sub(
        re.escape(amount_str) + r'\s*(?:dollars?|usd|eur|gbp|tk|bdt|rupees?)?',
        "", description, flags=re.IGNORECASE
    )
    description = re.sub(r'\s+', ' ', description).strip()
    description = re.sub(r'^(on|for|the|a|an)\s+', '', description, flags=re.IGNORECASE)

    if not description:
        description = "expense"

    return description.title()
