from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List

from . import register


@register("playwright_dynamic")
def collect(cfg: dict) -> dict:
    """
    本地 mock：不启动真实浏览器，仅模拟“可执行 JS/可获取渲染后数据”的能力。
    从页面内嵌 JSON payload 解析 items，代表 Playwright 渲染后可获得的数据。
    """
    start = time.perf_counter()
    errors: List[str] = []
    items: List[dict] = []

    base_dir = Path(cfg["base_dir"])
    entry = base_dir / cfg["entry"]

    try:
        # large mock: payload is stored in dynamic_payload.json, html only loads it at runtime
        payload_path = entry / "dynamic_payload.json" if entry.is_dir() else entry
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
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
    except Exception as e:
        errors.append(str(e))

    # 模拟：纯浏览器自动化直采，渲染与等待成本高于 XHR 复现，通常也高于「框架内接 Playwright」的摊销
    time.sleep(0.055)

    elapsed = time.perf_counter() - start
    return {
        "scenario": cfg["scenario"],
        "method": cfg["method"],
        "items": items,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 6),
        "resource_cost_score": int(cfg.get("resource_cost_score", 0)),
    }

