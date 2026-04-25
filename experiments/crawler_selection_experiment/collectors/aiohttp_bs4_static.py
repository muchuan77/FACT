from __future__ import annotations

import time
from pathlib import Path
from typing import List

from . import register
from .requests_bs4_static import _links_from_list, _read_text
from .static_detail_parse import detect_static_template, parse_static_detail


@register("aiohttp_bs4_static")
def collect(cfg: dict) -> dict:
    """
    在本地 mock_sources 下不做真实网络访问；
    该 collector 仅模拟“异步请求模型”的吞吐优势与一定工程复杂度成本。
    """
    start = time.perf_counter()
    errors: List[str] = []
    items: List[dict] = []

    base_dir = Path(cfg["base_dir"])
    entry = base_dir / cfg["entry"]

    try:
        list_pages = sorted(entry.glob("list_page_*.html")) if entry.is_dir() else [entry]
        detail_files: List[str] = []
        for lp in list_pages:
            detail_files.extend(_links_from_list(_read_text(lp)))

        # 模拟：批量并发带来的耗时降低
        for f in detail_files:
            detail_path = (entry / f) if entry.is_dir() else (entry.parent / f)
            detail_html = _read_text(detail_path)
            parsed = parse_static_detail(detail_html)
            tpl = detect_static_template(detail_html)
            items.append(
                {
                    "title": parsed["title"],
                    "content": parsed["content"],
                    "source": parsed["source"],
                    "source_url": parsed["source_url"],
                    "publish_time": parsed["publish_time"],
                    "category": parsed["category"],
                    "keywords": parsed["keywords"],
                    "_template": tpl,
                }
            )
    except Exception as e:
        errors.append(str(e))

    # 模拟：更低的平均延迟
    time.sleep(0.005)

    elapsed = time.perf_counter() - start
    return {
        "scenario": cfg["scenario"],
        "method": cfg["method"],
        "items": items,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 6),
        "resource_cost_score": int(cfg.get("resource_cost_score", 0)),
    }

