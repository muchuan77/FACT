from __future__ import annotations

import time
from pathlib import Path
from typing import List

from . import register
from .static_detail_parse import detect_static_template, parse_static_detail


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _extract_between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    if j < 0:
        return ""
    return text[i + len(start) : j].strip()


def _meta(content: str, name: str) -> str:
    # very small mock "BeautifulSoup" replacement
    key = f'<meta name="{name}" content="'
    return _extract_between(content, key, '"')


def _links_from_list(html: str) -> List[str]:
    links: List[str] = []
    pos = 0
    while True:
        a = html.find('href="', pos)
        if a < 0:
            break
        b = html.find('"', a + 6)
        if b < 0:
            break
        links.append(html[a + 6 : b])
        pos = b + 1
    return links


@register("requests_bs4_static")
def collect(cfg: dict) -> dict:
    start = time.perf_counter()
    errors: List[str] = []
    items: List[dict] = []

    base_dir = Path(cfg["base_dir"])
    entry = base_dir / cfg["entry"]

    try:
        # entry may be a directory containing list_page_*.html
        list_pages = []
        if entry.is_dir():
            list_pages = sorted(entry.glob("list_page_*.html"))
        else:
            list_pages = [entry]

        detail_files: List[str] = []
        for lp in list_pages:
            list_html = _read_text(lp)
            detail_files.extend(_links_from_list(list_html))

        for f in detail_files:
            detail_path = (entry / f) if entry.is_dir() else (entry.parent / f)
            detail_html = _read_text(detail_path)
            parsed = parse_static_detail(detail_html)
            parsed["_template"] = detect_static_template(detail_html)
            items.append(
                {
                    "title": parsed["title"],
                    "content": parsed["content"],
                    "source": parsed["source"],
                    "source_url": parsed["source_url"],
                    "publish_time": parsed["publish_time"],
                    "category": parsed["category"],
                    "keywords": parsed["keywords"],
                    "_template": parsed["_template"],
                }
            )
    except Exception as e:
        errors.append(str(e))

    # simulate small network latency
    time.sleep(0.01)

    elapsed = time.perf_counter() - start
    return {
        "scenario": cfg["scenario"],
        "method": cfg["method"],
        "items": items,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 6),
        "resource_cost_score": int(cfg.get("resource_cost_score", 0)),
    }

