from __future__ import annotations

from .base_adapter import AdapterContext
from .models import OpinionItem
from .rss_feedparser_adapter import RSSFeedparserAdapter
from .scrapy_playwright_dynamic_adapter import ScrapyPlaywrightDynamicAdapter
from .scrapy_static_adapter import ScrapyStaticAdapter


def _get_adapter(adapter_name: str):
    if adapter_name == "rss_feedparser":
        return RSSFeedparserAdapter()
    if adapter_name == "scrapy_static":
        return ScrapyStaticAdapter()
    if adapter_name == "scrapy_playwright_dynamic":
        return ScrapyPlaywrightDynamicAdapter()
    raise KeyError(f"unknown adapter_name: {adapter_name}")


def run_task_once(
    *,
    source_name: str,
    adapter_name: str,
    base_url: str,
    task_type: str,
    keywords: list[str],
    exclude_keywords: list[str],
    risk_words: list[str],
    category: str,
    max_items: int,
) -> list[OpinionItem]:
    adapter = _get_adapter(adapter_name)
    ctx = AdapterContext(
        source_name=source_name,
        base_url=base_url,
        task_type=task_type,
        keywords=keywords,
        exclude_keywords=exclude_keywords,
        risk_words=risk_words,
        category=category,
        max_items=max_items,
    )
    return adapter.fetch(ctx)

