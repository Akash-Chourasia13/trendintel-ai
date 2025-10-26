import hashlib

def review_uid_from(review_text: str, reviewer: str = "", date: str = "") -> str:
    base = (review_text or "") + "|" + (reviewer or "") + "|" + (date or "")
    return hashlib.md5(base.encode("utf-8")).hexdigest()