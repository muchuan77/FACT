from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import List

_NS_ENC = "{http://purl.org/rss/1.0/modules/content/}encoded"


def _strip_html(s: str) -> str:
    if not s:
        return ""
    t = re.sub(r"<[^>]+>", " ", s, flags=re.DOTALL)
    return " ".join(t.split()).strip()


def get_content_encoded_text(item: ET.Element) -> str:
    for child in item:
        if child.tag == _NS_ENC or child.tag.endswith("}encoded"):
            return (child.text or "").strip()
    return ""


def parse_rss_item_to_record(item: ET.Element, *, source_label: str = "模拟 RSS 信息源") -> dict:
    title = (item.findtext("title") or "").strip()
    link = (item.findtext("link") or "").strip()
    pub = (item.findtext("pubDate") or "").strip()
    cat = (item.findtext("category") or "").strip()
    desc = (item.findtext("description") or "").strip()
    encoded_raw = get_content_encoded_text(item)
    encoded_plain = _strip_html(encoded_raw)
    # 优先正文：content:encoded（去标签），其次 description，再次 summary
    summary_tag = (item.findtext("summary") or "").strip()
    content = encoded_plain or _strip_html(desc) or summary_tag
    kw_text = (item.findtext("keywords") or "").strip()
    keywords: List[str] = []
    if kw_text:
        for part in kw_text.replace("，", ",").split(","):
            p = part.strip()
            if p and p not in keywords:
                keywords.append(p)
    return {
        "title": title,
        "content": content,
        "source": source_label,
        "source_url": link,
        "publish_time": pub,
        "category": cat,
        "keywords": keywords,
    }
