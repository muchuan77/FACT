from __future__ import annotations

from .base_adapter import AdapterContext, BaseAdapter
from .models import OpinionItem


class ScrapyPlaywrightDynamicAdapter(BaseAdapter):
    """
    v1.5.0 实现：dynamic_page -> Scrapy + Playwright
    """

    adapter_name = "scrapy_playwright_dynamic"

    def fetch(self, ctx: AdapterContext) -> list[OpinionItem]:
        raise NotImplementedError("scrapy_playwright_dynamic_adapter is planned for v1.5.0")

