ALLOWED_TOPICS = {"customer", "customers", "transaction", "transactions", "payment", "payments", "spend", "spending", "analytics"}

def is_in_scope(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in ALLOWED_TOPICS)
