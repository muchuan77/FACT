from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Optional


def sha256_hex(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


# 典型 UTF-8 被误判为 latin-1 / 错误解码后出现的片段（用于入库前拦截）
_MOJIBAKE_MARKERS: tuple[str, ...] = (
    "\ufffd",  # U+FFFD
    "ï¿½",  # 常见替换对
    "Ä³",
    "æ¬",
    "Ã¤",
    "Ã¥",
)


def looks_like_mojibake(text: str) -> bool:
    """若文本含明显乱码片段，返回 True（用于跳过入库或打日志）。"""
    if not text:
        return False
    return any(m in text for m in _MOJIBAKE_MARKERS)


def clean_text_encoding_guard(text: str, *, label: str = "", url: str = "") -> str:
    """
    文本编码守卫：发现明显乱码时打 warning（不静默）。
    返回原文本（由调用方决定是否丢弃本条）。
    """
    import logging

    if looks_like_mojibake(text):
        logging.getLogger("fact_crawler.encoding").warning(
            "mojibake_detected label=%r url=%r sample=%r",
            label,
            url,
            (text or "")[:160],
        )
    return text


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


def parse_chinese_date_loose(s: str) -> Optional[datetime]:
    """
    解析常见中文日期片段，如「2024年01月15日」「2024年1月15日 10:30」。
    """
    if not s:
        return None

    s = (s or "").strip()
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    tm = re.search(r"(\d{1,2})\s*:\s*(\d{1,2})(?:\s*:\s*(\d{1,2}))?", s[m.end() :])
    if tm:
        hh, mm = int(tm.group(1)), int(tm.group(2))
        ss = int(tm.group(3) or 0)
        return datetime(y, mo, d, hh, mm, ss)
    return datetime(y, mo, d)

