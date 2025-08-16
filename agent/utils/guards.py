ALLOWED_TOPICS = {"customer", "customers", "transaction", "transactions", "payment", "payments", "spend", "spending", "analytics"}

def is_in_scope(text: str) -> bool:
    return True     # ToDO: Change this into a specific node with context.
    # t = (text or "").lower()
    # return any(k in t for k in ALLOWED_TOPICS)
