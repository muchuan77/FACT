from __future__ import annotations

from typing import Any

from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging

from .spider import PlaywrightDynamicSpider


def run_collect_raw(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """
    独立进程中执行 Scrapy + Playwright，返回原始 dict 列表（供 subprocess stdout JSON）。
    """
    configure_logging(install_root_handler=False)
    collector: list[dict[str, Any]] = []
    delay = max(0.0, float(cfg.get("rate_limit_seconds") or 0))
    settings: dict[str, Any] = {
        "USER_AGENT": "FACT-crawler/1.5 (+playwright) Mozilla/5.0 compatible",
        "ROBOTSTXT_OBEY": bool(cfg.get("robots_required", True)),
        "DOWNLOAD_DELAY": delay,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "PLAYWRIGHT_MAX_CONTEXTS": 2,
        "LOG_ENABLED": False,
        "COOKIES_ENABLED": False,
    }
    process = CrawlerProcess(settings)
    process.crawl(
        PlaywrightDynamicSpider,
        base_url=str(cfg.get("base_url") or ""),
        source_name=str(cfg.get("source_name") or ""),
        max_items=int(cfg.get("max_items") or 20),
        collector=collector,
    )
    process.start(stop_after_crawl=True)
    return collector
