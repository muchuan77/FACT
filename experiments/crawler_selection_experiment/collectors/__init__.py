from __future__ import annotations

from typing import Callable, Dict


CollectorFn = Callable[[dict], dict]


REGISTRY: Dict[str, CollectorFn] = {}


def register(name: str):
    def _wrap(fn: CollectorFn):
        REGISTRY[name] = fn
        return fn

    return _wrap


def get_collector(name: str) -> CollectorFn:
    if name not in REGISTRY:
        raise KeyError(f"collector not found: {name}")
    return REGISTRY[name]


# Auto-import collectors to populate REGISTRY.
# Note: 这里仅用于实验脚本，避免额外依赖/复杂动态加载。
from . import (  # noqa: E402,F401
    aiohttp_bs4_static,
    feedparser_rss_api,
    playwright_dynamic,
    requests_bs4_static,
    requests_dynamic,
    requests_rss_api,
    requests_xhr_dynamic,
    scrapy_dynamic,
    scrapy_playwright_dynamic,
    scrapy_rss_api,
    scrapy_static,
)

