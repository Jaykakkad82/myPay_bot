import hashlib

def idemp_key(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("||".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{h}"
