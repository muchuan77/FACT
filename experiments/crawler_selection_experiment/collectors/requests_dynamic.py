from __future__ import annotations

import time
from pathlib import Path
from typing import List

from . import register


@register("requests_dynamic")
def collect(cfg: dict) -> dict:
    """
    动态渲染页面：Requests 无法执行 JS，本 mock 仅能拿到壳页面，解析失败。
    """
    start = time.perf_counter()
    errors: List[str] = []
    items: List[dict] = []

    base_dir = Path(cfg["base_dir"])
    entry = base_dir / cfg["entry"]

    try:
        html_path = entry / "dynamic_sample.html" if entry.is_dir() else entry
        _ = html_path.read_text(encoding="utf-8")
        # 故意不解析：模拟无法执行 JS，拿不到渲染后的完整内容
    except Exception as e:
        errors.append(str(e))

    time.sleep(0.004)
    elapsed = time.perf_counter() - start
    return {
        "scenario": cfg["scenario"],
        "method": cfg["method"],
        "items": items,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 6),
        "resource_cost_score": int(cfg.get("resource_cost_score", 0)),
    }

