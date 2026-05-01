from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import feedparser
import requests

from .base_adapter import AdapterContext, BaseAdapter
from .keyword_extractor import extract_keywords
from .models import OpinionItem
from .normalizer import keyword_exclude, keyword_match, parse_datetime_loose


class RSSFeedparserAdapter(BaseAdapter):
    adapter_name = "rss_feedparser"

    def fetch(self, ctx: AdapterContext) -> list[OpinionItem]:
        print(f"[rss] source={ctx.source_name} url={ctx.base_url} max_items={ctx.max_items}")

        r = requests.get(ctx.base_url, timeout=10, headers={"User-Agent": "FACT-crawler/1.3 (rss validator)"})
        r.raise_for_status()
        d = feedparser.parse(r.content)
        entries = list(d.entries or [])

        print(
            f"[rss] source={ctx.source_name} entries_count={len(entries)} "
            f"feed_title={(getattr(d.feed, 'title', '') or '').strip()}"
        )

        out: list[OpinionItem] = []
        seen_url: set[str] = set()
        matched = 0

        for e in entries:
            title = (getattr(e, "title", "") or "").strip()
            link = (getattr(e, "link", "") or "").strip()
            summary = (getattr(e, "summary", "") or getattr(e, "description", "") or "").strip()
            published = (getattr(e, "published", "") or getattr(e, "updated", "") or "").strip()

            if not title or not link:
                continue
            if link in seen_url:
                continue

            if keyword_exclude(title, summary, ctx.exclude_keywords):
                continue
            if not keyword_match(title, summary, ctx.keywords):
                continue

            matched += 1
            seen_url.add(link)

            kws = extract_keywords(title, summary, risk_words=ctx.risk_words, limit=8)
            out.append(
                OpinionItem(
                    title=title,
                    content=summary or title,
                    source=ctx.source_name,
                    source_url=link,
                    publish_time=parse_datetime_loose(published),
                    category=ctx.category or "rss_news",
                    raw_label="rss",
                    keywords=kws,
                )
            )
            if len(out) >= ctx.max_items:
                break

        print(f"[rss] source={ctx.source_name} matched_count={matched} valid_count={len(out)}")
        return out

