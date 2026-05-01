from __future__ import annotations

from .base_adapter import AdapterContext, BaseAdapter
from .models import OpinionItem


class ScrapyStaticAdapter(BaseAdapter):
    """
    v1.4.0 实现：static_news -> Scrapy
    """

    adapter_name = "scrapy_static"

    def fetch(self, ctx: AdapterContext) -> list[OpinionItem]:
        raise NotImplementedError("scrapy_static_adapter is planned for v1.4.0")

