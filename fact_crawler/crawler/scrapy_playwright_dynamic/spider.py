from __future__ import annotations

import re
import sys
from urllib.parse import urlparse

import scrapy
from parsel import Selector
from scrapy import Spider
from scrapy_playwright.page import PageMethod

from ..normalizer import clean_text_encoding_guard, looks_like_mojibake


def _allowed_domain_from_netloc(netloc: str) -> str | None:
    netloc = (netloc or "").lower().strip()
    if not netloc:
        return None
    if netloc.startswith("["):
        end = netloc.find("]")
        if end == -1:
            return None
        return netloc[1:end]
    if ":" in netloc:
        return netloc.rsplit(":", 1)[0]
    return netloc


class PlaywrightDynamicSpider(Spider):
    """
    单页动态渲染：等待 JS 注入后，从 .opinion-card / .dynamic-item / [data-role=opinion-item] 抽取字段。
    """

    name = "fact_playwright_dynamic"

    def __init__(
        self,
        base_url: str,
        source_name: str,
        max_items: int,
        collector: list | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.base_url = (base_url or "").strip()
        self._source_name = source_name
        self.max_items = max(1, int(max_items))
        self.collector = collector if collector is not None else []
        self.start_urls = [self.base_url] if self.base_url else []
        bp = urlparse(self.base_url)
        base_dom = _allowed_domain_from_netloc(bp.netloc or "")
        self.allowed_domains = [base_dom] if base_dom else []

    def start_requests(self):
        if not self.start_urls:
            return
        url = self.start_urls[0]
        yield scrapy.Request(
            url,
            callback=self.parse_page,
            errback=self._err,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded"),
                    PageMethod("wait_for_timeout", 1200),
                    PageMethod(
                        "wait_for_selector",
                        ".opinion-card, .dynamic-item, [data-role=\"opinion-item\"]",
                        timeout=20000,
                        state="attached",
                    ),
                    PageMethod("wait_for_timeout", 400),
                ],
            },
            dont_filter=True,
        )

    def _err(self, failure):
        msg = f"[scrapy_playwright_dynamic] request_failed url={getattr(failure.request, 'url', '')!r} {failure}"
        print(msg, file=sys.stderr, flush=True)

    def _log_empty_diagnostics(self, response) -> None:
        text = (response.text or "") if hasattr(response, "text") else ""
        if not text and response.body:
            try:
                text = response.body.decode("utf-8", errors="replace")
            except Exception:
                text = ""
        sel = Selector(text=text)
        page_title = (sel.css("title::text").get() or "").strip()
        blocks = [x.strip() for x in (sel.css("body *::text").getall() or []) if x and x.strip()]
        links = sel.css("a::attr(href)").getall() or []
        msg = (
            "[scrapy_playwright_dynamic diagnostics]\n"
            f"  url={response.url!r}\n"
            f"  rendered_html_length={len(text)}\n"
            f"  page_title={page_title[:200]!r}\n"
            f"  detected_text_blocks_count={len(blocks)}\n"
            f"  detected_links_count={len(links)}\n"
            f"  text_head_300={text[:300]!r}\n"
        )
        print(msg, file=sys.stderr, flush=True)

    def parse_page(self, response):
        text = response.text or ""
        if not text and response.body:
            text = response.body.decode("utf-8", errors="replace")
        sel = Selector(text=text)

        cards = sel.css(".opinion-card, .dynamic-item, [data-role='opinion-item'], [data-role=\"opinion-item\"]")
        if not cards:
            self._log_empty_diagnostics(response)
            return

        page_url = response.url or self.base_url
        for card in cards:
            if len(self.collector) >= self.max_items:
                break
            title = (
                (card.css(".title::text").get() or "").strip()
                or (card.css("h2::text, h3::text").get() or "").strip()
            )
            parts = card.css(".content::text, p::text").getall() or []
            content = "\n".join(p.strip() for p in parts if p and p.strip())
            source = (card.css(".source::text").get() or "").strip() or self._source_name
            pub = (card.css(".publish-time::text, time::text").get() or "").strip()
            category = (card.css(".category::text").get() or "").strip()
            kw_attr = (card.css("::attr(data-keywords)").get() or "").strip()
            kw_parts = [x.strip() for x in (card.css(".keyword::text").getall() or []) if x.strip()]
            if kw_attr and not kw_parts:
                kw_parts = [k.strip() for k in re.split(r"[,，]", kw_attr) if k.strip()]
            href = (card.css("a.detail::attr(href)").get() or "").strip()
            source_url = href or page_url

            if not title or len(content) < 4:
                continue

            clean_text_encoding_guard(title, label="title", url=source_url)
            clean_text_encoding_guard(content, label="content", url=source_url)
            host = (urlparse(source_url).hostname or "").lower()
            if host in ("127.0.0.1", "localhost", "::1", "0.0.0.0"):
                if looks_like_mojibake(title) or looks_like_mojibake(content):
                    continue

            self.collector.append(
                {
                    "title": title,
                    "content": content,
                    "source_url": source_url,
                    "publish_time_str": pub,
                    "page_category": category,
                    "article_source": source,
                    "html_keywords": kw_parts[:16],
                }
            )
