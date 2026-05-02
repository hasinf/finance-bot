CATEGORIES = {
    "Food & Drinks": [
        "coffee", "tea", "latte", "cappuccino", "espresso", "brew",
        "food", "lunch", "dinner", "breakfast", "brunch", "snack",
        "restaurant", "cafe", "bistro", "eatery", "diner",
        "pizza", "burger", "sandwich", "salad", "pasta", "rice",
        "noodle", "sushi", "taco", "kebab", "biriyani", "curry",
        "croissant", "pastry", "bakery", "bread", "cake",
        "drink", "juice", "smoothie", "milkshake", "soda", "beer",
        "wine", "alcohol", "cocktail", "water",
        "grocery", "supermarket", "market", "vegetable", "fruit",
        "chicken", "meat", "fish", "seafood", "egg", "cheese",
        "sweet", "dessert", "ice cream", "chocolate", "candy",
        "restaurant", "takeout", "takeaway", "delivery", "doordash",
        "ubereats", "grubhub", "hungrynaki", "foodpanda",
    ],
    "Transport": [
        "uber", "lyft", "grab", "taxi", "cab", "ride",
        "bus", "train", "metro", "subway", "tram",
        "flight", "airplane", "airport", "airline",
        "gas", "fuel", "petrol", "diesel", "charging",
        "parking", "toll", "highway",
        "bike", "bicycle", "scooter", "motorcycle",
        "car", "vehicle", "rental", "lease",
        "pathao", "shohoz", "transport", "commute",
        "ticket", "fare", "pass",
    ],
    "Entertainment": [
        "movie", "cinema", "film", "theater", "theatre",
        "concert", "show", "performance", "play", "musical",
        "game", "gaming", "playstation", "xbox", "nintendo",
        "netflix", "spotify", "youtube", "disney", "hulu",
        "subscription", "streaming",
        "book", "novel", "magazine", "newspaper",
        "museum", "gallery", "exhibition",
        "park", "zoo", "aquarium", "amusement", "theme park",
        "sport", "gym", "fitness", "yoga", "swimming",
        "event", "festival", "party", "club", "bar",
        "hobby", "craft", "art",
    ],
    "Shopping": [
        "clothes", "clothing", "shirt", "pants", "dress", "shoes",
        "jacket", "coat", "hat", "accessories", "jewelry",
        "electronics", "phone", "laptop", "computer", "tablet",
        "headphone", "charger", "cable", "gadget",
        "furniture", "home", "decor", "appliance",
        "cosmetic", "makeup", "skincare", "perfume",
        "gift", "present",
        "mall", "shop", "store", "marketplace", "amazon",
        "online", "order", "purchase", "buy",
    ],
    "Personal": [
        "haircut", "hair", "salon", "barber", "beauty",
        "doctor", "hospital", "clinic", "medicine", "pharmacy",
        "health", "medical", "dental", "eye", "vision",
        "insurance", "therapy", "counseling",
        "education", "course", "class", "tuition", "school",
        "university", "college", "training",
    ],
    "Bills": [
        "rent", "mortgage", "lease",
        "electricity", "electric", "power", "utility",
        "water", "gas bill",
        "internet", "wifi", "broadband", "isp",
        "phone bill", "mobile bill", "recharge",
        "cable", "tv bill",
        "insurance", "tax", "fee",
        "subscription", "membership", "dues",
        "maintenance", "repair", "service charge",
    ],
}

CATEGORY_NAMES = list(CATEGORIES.keys())
DEFAULT_CATEGORY = "Misc"


def detect_category(text: str) -> str:
    text_lower = text.lower()

    scores = {}
    for category, keywords in CATEGORIES.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
                if text_lower.startswith(keyword):
                    score += 2
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)

    return DEFAULT_CATEGORY
