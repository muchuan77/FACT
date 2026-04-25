from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from . import register
from .rss_item_utils import parse_rss_item_to_record


@register("requests_rss_api")
def collect(cfg: dict) -> dict:
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
            items.append(parse_rss_item_to_record(it))
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

