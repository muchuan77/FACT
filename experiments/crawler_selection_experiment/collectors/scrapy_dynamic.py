from __future__ import annotations

import time
from pathlib import Path
from typing import List

from . import register


@register("scrapy_dynamic")
def collect(cfg: dict) -> dict:
    """
    动态渲染页面：Scrapy 默认不执行 JS。
    本 mock 仅模拟其抓取框架能力，但在动态内容场景仍解析失败。
    """
    start = time.perf_counter()
    errors: List[str] = []
    items: List[dict] = []

    base_dir = Path(cfg["base_dir"])
    entry = base_dir / cfg["entry"]

    try:
        html_path = entry / "dynamic_sample.html" if entry.is_dir() else entry
        _ = html_path.read_text(encoding="utf-8")
        # 故意不解析：模拟 Scrapy 默认不执行 JS
    except Exception as e:
        errors.append(str(e))

    time.sleep(0.006)
    elapsed = time.perf_counter() - start
    return {
        "scenario": cfg["scenario"],
        "method": cfg["method"],
        "items": items,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 6),
        "resource_cost_score": int(cfg.get("resource_cost_score", 0)),
    }

