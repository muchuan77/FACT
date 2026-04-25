from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List

from . import register


def _items_from_payload(payload: dict) -> List[dict]:
    items: List[dict] = []
    for it in (payload.get("items", []) or []):
        items.append(
            {
                "title": it.get("title", ""),
                "content": it.get("content", ""),
                "source": it.get("source", ""),
                "source_url": it.get("source_url", ""),
                "publish_time": it.get("publish_time", ""),
                "category": it.get("category", ""),
                "keywords": it.get("keywords", []) or [],
                "summary": it.get("summary", "") or "",
            }
        )
    return items


@register("scrapy_playwright_dynamic")
def collect(cfg: dict) -> dict:
    """
    模拟 Scrapy 调度体系下接入 Playwright 渲染（本地 mock：读取渲染后可得的 payload）。
    代表工程化动态采集：兼顾调度/去重/Pipeline 与 JS 渲染，适合长期舆情采集。
    """
    start = time.perf_counter()
    errors: List[str] = []
    items: List[dict] = []

    base_dir = Path(cfg["base_dir"])
    entry = base_dir / cfg["entry"]

    try:
        payload_path = entry / "dynamic_payload.json" if entry.is_dir() else entry
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        items = _items_from_payload(payload)
    except Exception as e:
        errors.append(str(e))

    # 模拟：Scrapy 调度 + Playwright 启动/渲染的中间开销（低于纯浏览器直开全量交互）
    time.sleep(0.018)

    elapsed = time.perf_counter() - start
    return {
        "scenario": cfg["scenario"],
        "method": cfg["method"],
        "items": items,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 6),
        "resource_cost_score": int(cfg.get("resource_cost_score", 0)),
    }
