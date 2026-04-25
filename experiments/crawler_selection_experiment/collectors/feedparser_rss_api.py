from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from . import register
from .rss_item_utils import parse_rss_item_to_record


def _simple_keyword_hint(text: str) -> list[str]:
    bank = ["网传", "爆料", "谣言", "不实", "恐慌", "事故", "火灾", "地震", "疫情", "食品安全", "诈骗"]
    hits = []
    for w in bank:
        if w in text and w not in hits:
            hits.append(w)
    return hits[:5]


@register("feedparser_rss_api")
def collect(cfg: dict) -> dict:
    """
    本地 mock：用更“面向 RSS 的字段解析”模拟 feedparser 的优势。
    """
    start = time.perf_counter()
    errors: List[str] = []
    items: List[dict] = []

    base_dir = Path(cfg["base_dir"])
    entry = base_dir / cfg["entry"]

    try:
        xml_path = entry / "sample_feed.xml" if entry.is_dir() else entry
        xml_text = xml_path.read_text(encoding="utf-8")
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            raise ValueError("no channel")

        for it in channel.findall("item"):
            rec = parse_rss_item_to_record(it)
            if not rec["keywords"]:
                rec["keywords"] = _simple_keyword_hint(rec["title"] + " " + rec["content"])
            items.append(rec)
    except Exception as e:
        errors.append(str(e))

    time.sleep(0.002)
    elapsed = time.perf_counter() - start
    return {
        "scenario": cfg["scenario"],
        "method": cfg["method"],
        "items": items,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 6),
        "resource_cost_score": int(cfg.get("resource_cost_score", 0)),
    }

