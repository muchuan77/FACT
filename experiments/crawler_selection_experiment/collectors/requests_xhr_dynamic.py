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


@register("requests_xhr_dynamic")
def collect(cfg: dict) -> dict:
    """
    模拟通过 Network 面板定位 XHR/API 后直接复现请求（本地 mock 读取 dynamic_payload.json）。
    代表轻量接口复现方案：吞吐高、资源低，但依赖接口可发现性与长期维护。
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

    # 模拟：仅 HTTP JSON，无浏览器；成本远低于渲染方案
    time.sleep(0.003)

    elapsed = time.perf_counter() - start
    return {
        "scenario": cfg["scenario"],
        "method": cfg["method"],
        "items": items,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 6),
        "resource_cost_score": int(cfg.get("resource_cost_score", 0)),
    }
