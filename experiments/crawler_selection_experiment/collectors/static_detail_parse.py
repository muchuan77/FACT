"""
从 FACT 爬虫选型实验的 mock 静态详情页中提取字段。
支持五类模板（新闻门户 / 政务通报 / 论坛帖子 / 校园公告 / 本地生活）及噪声页的兜底选择器。
"""
from __future__ import annotations

import json
import re
from typing import List, Tuple


def _strip_tags(html_fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html_fragment, flags=re.IGNORECASE | re.DOTALL)
    return " ".join(text.split()).strip()


def _first_group(patterns: list[tuple[str, int]], html: str) -> str:
    for pat, group_idx in patterns:
        m = re.search(pat, html, flags=re.IGNORECASE | re.DOTALL)
        if m:
            g = m.group(group_idx).strip()
            if g:
                return _strip_tags(g) if "<" in g else g.strip()
    return ""


def _extract_between(html: str, start: str, end: str) -> str:
    i = html.find(start)
    if i < 0:
        return ""
    j = html.find(end, i + len(start))
    if j < 0:
        return ""
    return html[i + len(start) : j].strip()


def _meta_name(content: str, name: str) -> str:
    key = f'<meta name="{name}" content="'
    return _extract_between(content, key, '"')


def _meta_property(content: str, prop: str) -> str:
    m = re.search(
        rf'<meta\s+property="{re.escape(prop)}"\s+content="([^"]*)"',
        content,
        flags=re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def _split_keywords(raw: str) -> List[str]:
    if not raw:
        return []
    raw = raw.replace("，", ",")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _extract_json_ld_headline(html: str) -> str:
    m = re.search(
        r'<script[^>]*type="application/ld\+json"[^>]*>\s*(\{.*?\})\s*</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return ""
    try:
        data = json.loads(m.group(1))
        if isinstance(data, dict):
            h = data.get("headline")
            return str(h).strip() if h else ""
    except json.JSONDecodeError:
        pass
    return ""


def _time_datetime_from_class(html: str) -> str:
    """匹配 class 中含 publish-time / notice-time 等多 class 组合的 <time datetime=\"...\">。"""
    time_class_pat = r"(?:publish-time|notice-time|post-time|campus-time|feed-time)"
    patterns = [
        rf'<time[^>]*class="[^"]*{time_class_pat}[^"]*"[^>]*datetime="([^"]+)"',
        rf'<time[^>]*datetime="([^"]+)"[^>]*class="[^"]*{time_class_pat}[^"]*"',
    ]
    for pat in patterns:
        m = re.search(pat, html, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
    return ""


def _time_inner_text(html: str) -> str:
    time_class_pat = r"(?:publish-time|notice-time|post-time|campus-time|feed-time)"
    m = re.search(
        rf'<time[^>]*class="[^"]*{time_class_pat}[^"]*"[^>]*>(.*?)</time>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        return _strip_tags(m.group(1))
    return ""


def _span_time_text(html: str, class_names: Tuple[str, ...]) -> str:
    for cn in class_names:
        m = re.search(
            rf'<span[^>]*class="[^"]*{re.escape(cn)}[^"]*"[^>]*>(.*?)</span>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if m:
            t = _strip_tags(m.group(1))
            if t:
                return t
    return ""


def _div_block_by_class(html: str, cls: str) -> str:
    """匹配 class 属性中含 cls 的 div 块内 HTML（非贪婪到第一个闭合 div，适用于 mock 正文区无嵌套 div）。"""
    m = re.search(
        rf'<div[^>]*class="[^"]*\b{re.escape(cls)}\b[^"]*"[^>]*>(.*?)</div>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return m.group(1) if m else ""


def _section_by_class(html: str, cls: str) -> str:
    m = re.search(
        rf'<section[^>]*class="[^"]*\b{re.escape(cls)}\b[^"]*"[^>]*>(.*?)</section>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return m.group(1) if m else ""


def _main_or_article_inner(html: str, tag: str) -> str:
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    inner = m.group(1)
    # 去掉 script/style 以免污染正文
    inner = re.sub(r"<script[^>]*>.*?</script>", " ", inner, flags=re.IGNORECASE | re.DOTALL)
    inner = re.sub(r"<style[^>]*>.*?</style>", " ", inner, flags=re.IGNORECASE | re.DOTALL)
    return _strip_tags(inner)


def detect_static_template(html: str) -> str:
    """根据页面骨架判断模板类型，用于实验统计。"""
    if re.search(r'class="[^"]*\barticle-title\b', html):
        return "A_news_portal"
    if re.search(r'class="[^"]*\bnotice-title\b', html):
        return "B_gov_notice"
    if "forum-wrap" in html and re.search(r'class="[^"]*\bpost-title\b', html):
        return "C_forum_post"
    if re.search(r'class="[^"]*\bcampus-title\b', html):
        return "D_campus"
    if "local-feed" in html and re.search(r'class="[^"]*\bfeed-title\b', html):
        return "E_local_feed"
    return "unknown_noise_or_legacy"


def parse_static_detail(detail_html: str) -> dict:
    """解析一条静态详情页，返回与实验一致的字段字典。"""
    title_patterns: list[tuple[str, int]] = [
        (r'<h1[^>]*class="[^"]*\barticle-title\b[^"]*"[^>]*>(.*?)</h1>', 1),
        (r'<h1[^>]*class="[^"]*\bnotice-title\b[^"]*"[^>]*>(.*?)</h1>', 1),
        (r'<h1[^>]*class="[^"]*\bcampus-title\b[^"]*"[^>]*>(.*?)</h1>', 1),
        (r'<div[^>]*class="[^"]*\bpost-title\b[^"]*"[^>]*>(.*?)</div>', 1),
        (r'<h2[^>]*class="[^"]*\bfeed-title\b[^"]*"[^>]*>(.*?)</h2>', 1),
        (r'<meta\s+property="og:title"\s+content="([^"]*)"', 1),
        (r'<meta\s+property="twitter:title"\s+content="([^"]*)"', 1),
        (r"<h1[^>]*>(.*?)</h1>", 1),
        (r"<title>(.*?)</title>", 1),
    ]
    title = _first_group(title_patterns, detail_html)
    if not title:
        title = _extract_json_ld_headline(detail_html)
    if " - " in title and title.count(" - ") >= 1:
        title = title.split(" - ")[0].strip()

    content = ""
    # 正文：优先 section / 各模板主容器，再 article / main
    for inner in (
        _section_by_class(detail_html, "article-content"),
        _div_block_by_class(detail_html, "notice-body"),
        _div_block_by_class(detail_html, "post-body"),
        _div_block_by_class(detail_html, "campus-content"),
        _div_block_by_class(detail_html, "feed-content"),
        _div_block_by_class(detail_html, "article-content"),
        _div_block_by_class(detail_html, "content"),
        _div_block_by_class(detail_html, "main-text"),
        _div_block_by_class(detail_html, "unknown-body"),
    ):
        if inner:
            content = _strip_tags(inner)
            if content:
                break
    if not content:
        content = _main_or_article_inner(detail_html, "article") or _main_or_article_inner(detail_html, "main")

    source = _first_group(
        [
            (r'<span[^>]*class="[^"]*\bsource\b[^"]*"[^>]*>(.*?)</span>', 1),
            (r'<div[^>]*class="[^"]*\bsource\b[^"]*"[^>]*>(.*?)</div>', 1),
            (r'<span[^>]*class="[^"]*\bnotice-source\b[^"]*"[^>]*>(.*?)</span>', 1),
        ],
        detail_html,
    )
    for prefix in ("来源：", "信息来源："):
        if source.startswith(prefix):
            source = source[len(prefix) :].strip()
    if not source:
        # post-meta / campus-meta / feed-meta 内第一个 span.source
        for block_cls in ("post-meta", "campus-meta", "feed-meta"):
            block = _div_block_by_class(detail_html, block_cls)
            if block:
                m = re.search(
                    r'<span[^>]*class="[^"]*\bsource\b[^"]*"[^>]*>(.*?)</span>',
                    block,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                if m:
                    source = _strip_tags(m.group(1))
                    for prefix in ("来源：", "信息来源："):
                        if source.startswith(prefix):
                            source = source[len(prefix) :].strip()
                    if source:
                        break
    if not source:
        source = _meta_name(detail_html, "source")

    publish_time = _time_datetime_from_class(detail_html)
    if not publish_time:
        publish_time = _time_inner_text(detail_html)
    if not publish_time:
        publish_time = _span_time_text(
            detail_html,
            ("publish-time", "notice-time", "post-time", "campus-time", "feed-time"),
        )
    if not publish_time:
        publish_time = _meta_name(detail_html, "publish_time")
    if not publish_time:
        publish_time = _meta_property(detail_html, "article:published_time")

    category = _first_group([(r'<span[^>]*class="[^"]*\bcategory\b[^"]*"[^>]*>(.*?)</span>', 1)], detail_html)
    if not category:
        category = _meta_name(detail_html, "category")

    kw_raw = _meta_name(detail_html, "keywords")
    keywords = _split_keywords(kw_raw)
    if not keywords:
        for pat in (
            r'<footer[^>]*class="[^"]*\barticle-footer\b[^"]*"[^>]*>(.*?)</footer>',
            r'<div[^>]*class="[^"]*\bkeywords\b[^"]*"[^>]*>(.*?)</div>',
        ):
            m = re.search(pat, detail_html, flags=re.IGNORECASE | re.DOTALL)
            if m:
                block = m.group(1)
                m2 = re.search(r"关键词[：:]\s*([^<]+)", block)
                if m2:
                    keywords = _split_keywords(m2.group(1).split("。")[0])
                    if keywords:
                        break
    if not keywords:
        m3 = re.search(r"关键词[：:]\s*([^<]+)", detail_html)
        if m3:
            keywords = _split_keywords(m3.group(1).split("。")[0])
    if not keywords:
        kws_spans = re.findall(
            r'<span[^>]*class="[^"]*\bkeyword\b[^"]*"[^>]*>(.*?)</span>',
            detail_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        keywords = _split_keywords(",".join(_strip_tags(x) for x in kws_spans if x.strip()))

    source_url = ""
    m4 = re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', detail_html, flags=re.IGNORECASE)
    if m4:
        source_url = m4.group(1).strip()
    if not source_url:
        source_url = _extract_between(detail_html, '<div class="source-url">', "</div>")
    if not source_url:
        m5 = re.search(r'<a[^>]*class="[^"]*\bpermalink\b[^"]*"[^>]*href="([^"]+)"', detail_html, flags=re.IGNORECASE)
        if m5:
            source_url = m5.group(1).strip()

    return {
        "title": title,
        "content": content,
        "source": source,
        "source_url": source_url,
        "publish_time": publish_time,
        "category": category,
        "keywords": keywords,
    }
