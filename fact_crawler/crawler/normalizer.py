from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional


def sha256_hex(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def keyword_match(title: str, content: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text = f"{title} {content}"
    return any((k and k in text) for k in keywords)


def keyword_exclude(title: str, content: str, exclude_keywords: list[str]) -> bool:
    if not exclude_keywords:
        return False
    text = f"{title} {content}"
    return any((k and k in text) for k in exclude_keywords)


def parse_datetime_loose(s: str) -> Optional[datetime]:
    if not s:
        return None
    # very loose: try ISO first, else return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

