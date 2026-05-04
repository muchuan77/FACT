from __future__ import annotations

import re
import sys
from urllib.parse import urljoin, urlparse

from parsel import Selector
from scrapy import Request, Spider

from ..normalizer import clean_text_encoding_guard, looks_like_mojibake


def _allowed_domain_from_netloc(netloc: str) -> str | None:
    """
    Scrapy Offsite 中间件只接受「无端口」域名；带端口如 127.0.0.1:8765 会被整项忽略，
    导致 host 正则匹配失败、所有请求被滤掉（total_fetched=0）。
    """
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


class StaticNewsSpider(Spider):
    """
    静态列表页 → 详情页：支持中国政府网政策栏目、本地 list.html 演示、同域通用列表。

    对本机 http.server：不得使用 response.text / response.css（依赖 Scrapy 误判的 encoding），
    必须用 response.body.decode("utf-8", errors="strict") + parsel.Selector(text=html)。
    """

    name = "fact_static_news"

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
        self._seen_detail: set[str] = set()
        self.start_urls = [self.base_url] if self.base_url else []
        self._detail_goal = max(40, self.max_items * 12)

        bp = urlparse(self.base_url)
        base_dom = _allowed_domain_from_netloc(bp.netloc or "")
        hosts: set[str] = set()
        if base_dom:
            hosts.add(base_dom)
        if base_dom and "gov.cn" in base_dom:
            hosts.update({"www.gov.cn", "gov.cn"})
        self.allowed_domains = sorted(hosts)

    @staticmethod
    def _is_localhost_url(url: str) -> bool:
        host = (urlparse(url).hostname or "").lower()
        return host in ("127.0.0.1", "localhost", "::1", "0.0.0.0")

    @staticmethod
    def _is_gov_zhengce_policy_url(url: str) -> bool:
        p = urlparse(url)
        pl = p.path.lower()
        if "gov.cn" not in p.netloc.lower():
            return False
        pln = pl.rstrip("/")
        return pl.startswith("/zhengce/") or pln == "/zhengce"

    def _decoded_selector(self, response):
        """
        返回 (parsel.Selector, used_encoding_label)。
        本机：UTF-8 严格解码 body + Selector(text=html) -> utf-8-forced。
        远端：沿用 Scrapy 的 response.selector 与自动 encoding。
        """
        ct_b = response.headers.get(b"Content-Type") or b""
        ct = ct_b.decode("latin-1", errors="replace")
        enc = response.encoding or ""
        host = (urlparse(response.url).hostname or "").lower()
        is_local = host in ("127.0.0.1", "localhost", "0.0.0.0", "::1")
        self.logger.info(
            "response_meta url=%s scrapy_encoding=%r Content-Type=%r is_local=%s",
            response.url,
            enc,
            ct[:200],
            is_local,
        )
        if is_local:
            html = response.body.decode("utf-8", errors="strict")
            sel = Selector(text=html)
            used = "utf-8-forced"
            self.logger.info("decoded_selector used_encoding=%s url=%s", used, response.url)
            return sel, used
        sel = response.selector
        used = response.encoding or "auto"
        self.logger.info("decoded_selector used_encoding=%s url=%s", used, response.url)
        return sel, used

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse_list, errback=self._err, dont_filter=False)

    def _err(self, failure):
        self.logger.warning("request_failed %s", failure)

    def parse_list(self, response):
        sel, _used_enc = self._decoded_selector(response)
        mode = self._detect_list_mode(response)
        all_hrefs = sel.css("a::attr(href)").getall() or []

        if mode == "gov_zhengce":
            links = self._links_gov_policy(sel, response.url)
            self._log_gov_zhengce_list_diagnostics(response, sel, all_hrefs, links)
        elif mode == "demo_list":
            links = self._links_demo_list(sel, response.url)
        else:
            links = self._links_generic(sel, response.url)

        if not links:
            if mode == "generic":
                rec = self._record_from_detail(response, sel)
                if rec:
                    self._append_record(rec)
            return

        for href in links:
            if len(self.collector) >= self._detail_goal:
                break
            yield response.follow(href, callback=self.parse_detail, errback=self._err)

    def parse_detail(self, response):
        sel, _used_enc = self._decoded_selector(response)
        rec = self._record_from_detail(response, sel)
        if rec:
            self._append_record(rec)

    def _append_record(self, rec: dict) -> None:
        url = rec.get("source_url") or ""
        if not url or url in self._seen_detail:
            return
        self._seen_detail.add(url)
        if len(self.collector) >= self._detail_goal:
            return
        self.collector.append(rec)

    def _log_gov_zhengce_list_diagnostics(
        self, response, sel: Selector, all_hrefs: list[str], links: list[str]
    ) -> None:
        if "gov.cn" not in response.url.lower() or "zhengce" not in response.url.lower():
            return
        ct = (response.headers.get(b"Content-Type") or b"").decode("latin-1", errors="replace")
        page_title = (sel.css("title::text").get() or "").strip()[:300]
        raw_preview = [urljoin(response.url, (x or "").strip()) for x in all_hrefs[:20]]
        msg = (
            "[gov.cn zhengce list diagnostics]\n"
            f"  list_page_response.status={response.status}\n"
            f"  response.url={response.url!r}\n"
            f"  response.encoding={response.encoding!r}\n"
            f"  Content-Type={ct[:220]!r}\n"
            f"  page_title={page_title[:200]!r}\n"
            f"  a_href_total={len(all_hrefs)}\n"
            f"  href_preview_first20={raw_preview!r}\n"
            f"  detail_links_count={len(links)}\n"
            f"  detail_links_first10={links[:10]!r}\n"
        )
        if not links:
            msg += "  reason: gov.cn list page reached but no detail links extracted\n"
        print(msg, file=sys.stderr, flush=True)

    def _log_gov_detail_skip(self, url: str, title: str, body_len: int) -> None:
        print(
            f"[gov.cn zhengce detail skip] url={url!r} title_empty={not (title or '').strip()} "
            f"body_len={body_len} (title/body too short or empty after extract)\n",
            file=sys.stderr,
            flush=True,
        )

    def _detect_list_mode(self, response):
        u = (response.url or "").lower()
        host = urlparse(u).netloc.lower()
        if "gov.cn" in host and "zhengce" in u:
            return "gov_zhengce"
        if u.endswith("list.html") or u.rstrip("/").split("/")[-1] == "list.html":
            return "demo_list"
        return "generic"

    def _gov_policy_link_excluded(self, full: str, page_url: str) -> bool:
        """排除列表/索引/分页入口等，不强制 URL 含 content_。"""
        base = page_url.split("#")[0].rstrip("/")
        if full.split("#")[0].rstrip("/") == base:
            return True
        path = urlparse(full).path.lower()
        seg = path.rstrip("/").split("/")[-1] if path else ""
        if seg in ("index.htm", "index.html", "index.shtml"):
            return True
        if seg.startswith("list") and seg.endswith((".htm", ".html", ".shtml")) and len(seg) <= 20:
            return True
        if re.search(r"/list[_\d]*\.(htm|html|shtml)$", path):
            return True
        if re.search(r"/index[_\d]*\.(htm|html|shtml)$", path):
            return True
        return False

    def _links_gov_policy(self, sel: Selector, page_url: str) -> list[str]:
        """
        gov.cn + 路径含 /zhengce/ + 常见正文后缀；不强制 content_；去重保序。
        """
        out: list[str] = []
        seen: set[str] = set()
        for href in sel.css("a::attr(href)").getall() or []:
            h = (href or "").strip()
            if not h:
                continue
            full = urljoin(page_url, h).split("#")[0]
            if full.startswith("//"):
                full = "https:" + full
            low = full.lower()
            if not full.startswith("http"):
                continue
            if "javascript:" in low or "mailto:" in low:
                continue
            if "gov.cn" not in urlparse(full).netloc.lower():
                continue
            path = urlparse(full).path.lower()
            pn = path.rstrip("/")
            if not (path.startswith("/zhengce/") or pn == "/zhengce"):
                continue
            if not low.endswith((".htm", ".html", ".shtml")):
                continue
            if self._gov_policy_link_excluded(full, page_url):
                continue
            if full not in seen:
                seen.add(full)
                out.append(full)
            if len(out) >= self._detail_goal:
                break
        return out[: self._detail_goal]

    def _links_demo_list(self, sel: Selector, page_url: str) -> list[str]:
        base_netloc = urlparse(page_url).netloc.lower()
        out: list[str] = []
        for href in sel.css("a::attr(href)").getall() or []:
            full = urljoin(page_url, (href or "").strip())
            if urlparse(full).netloc.lower() != base_netloc:
                continue
            if full.rstrip("/") == page_url.rstrip("/"):
                continue
            low = full.lower()
            if low.endswith(("list.html", "index.html")):
                continue
            if low.endswith((".html", ".htm")):
                out.append(full)
        seen: set[str] = set()
        uniq: list[str] = []
        for x in out:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        return uniq[: self._detail_goal]

    def _links_generic(self, sel: Selector, page_url: str) -> list[str]:
        base_host = urlparse(page_url).netloc.lower()
        out: list[str] = []
        for href in sel.css("a::attr(href)").getall() or []:
            full = urljoin(page_url, (href or "").strip())
            if urlparse(full).netloc.lower() != base_host:
                continue
            low = full.lower()
            if low.endswith((".pdf", ".zip", ".jpg", ".png", ".gif", ".js", ".css")):
                continue
            if full.split("#")[0].rstrip("/") == page_url.split("#")[0].rstrip("/"):
                continue
            full = full.split("#")[0]
            out.append(full)
        seen: set[str] = set()
        uniq: list[str] = []
        for x in out:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        return uniq[: self._detail_goal]

    def _record_from_detail(self, response, sel: Selector) -> dict | None:
        url = response.url or ""
        if url in self._seen_detail:
            return None

        mode = "gov" if self._is_gov_zhengce_policy_url(url) else "generic"
        ex = self._extract_gov(sel) if mode == "gov" else self._extract_generic(sel)
        title = (ex.get("title") or "").strip()
        body = (ex.get("body") or "").strip()
        if not title or len(body) < 8:
            if mode == "gov":
                self._log_gov_detail_skip(url, title, len(body))
            return None

        clean_text_encoding_guard(title, label="title", url=url)
        clean_text_encoding_guard(body, label="content", url=url)
        if self._is_localhost_url(url):
            if looks_like_mojibake(title) or looks_like_mojibake(body):
                self.logger.error(
                    "mojibake_skip_local_demo url=%s title_sample=%r body_sample=%r",
                    url,
                    title[:100],
                    body[:100],
                )
                return None

        return {
            "title": title,
            "content": body or title,
            "source_url": url,
            "publish_time_str": (ex.get("publish_time_str") or "").strip(),
            "page_category": (ex.get("page_category") or "").strip(),
            "article_source": (ex.get("article_source") or "").strip(),
            "html_keywords": list(ex.get("html_keywords") or []),
        }

    def _extract_gov(self, sel: Selector) -> dict:
        title = (
            (sel.css("h1::text").get() or "").strip()
            or (sel.css(".article-title::text").get() or "").strip()
            or (sel.css('meta[property="og:title"]::attr(content)').get() or "").strip()
            or (sel.css("title::text").get() or "").strip()
        )

        body_chunks: list[str] = []
        for css in (
            "#UCAP-CONTENT *::text",
            ".pages_content *::text",
            ".article-content *::text",
            "article *::text",
            "main *::text",
            "p::text",
        ):
            parts = sel.css(css).getall() or []
            chunk = "\n".join(p.strip() for p in parts if p and p.strip())
            if chunk:
                body_chunks.append(chunk)
        body = "\n\n".join(body_chunks)
        if len(body) > 50000:
            body = body[:50000]

        pub_s = (
            (sel.css(".pages-date::text").get() or "").strip()
            or (sel.css(".time::text").get() or "").strip()
            or (sel.css("#docData time::text").get() or "").strip()
            or (sel.css('meta[name="PubDate"]::attr(content)').get() or "").strip()
        )
        if not pub_s:
            blob = " ".join((sel.css("body *::text").getall() or [])[:400])
            m = re.search(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", blob[:8000])
            if m:
                pub_s = m.group(0).strip()

        article_source = (sel.css(".source::text").get() or "").strip() or (sel.css(".pages-source::text").get() or "").strip()
        if not article_source:
            for line in (sel.xpath("//body//text()").getall() or [])[:400]:
                t = (line or "").strip()
                if "来源：" in t or "来源:" in t:
                    article_source = t[:300]
                    break

        crumbs = sel.css(".breadcrumb a::text, .BreadcrumbNav a::text").getall()
        cat = " > ".join(x.strip() for x in crumbs if x.strip())[:200]

        return {
            "title": title,
            "body": body,
            "publish_time_str": pub_s,
            "page_category": cat,
            "article_source": article_source,
            "html_keywords": [],
        }

    def _extract_generic(self, sel: Selector) -> dict:
        title = sel.css("h1::text").get() or sel.css("title::text").get()
        title = (title or "").strip()
        parts = sel.css(
            "article .body *::text, article section *::text, article p::text, article *::text, "
            "main *::text, .content *::text, #content *::text, p::text"
        ).getall()
        if not parts:
            parts = sel.xpath("//body//text()").getall()
        body = "\n".join(p.strip() for p in parts if p and p.strip())
        if len(body) > 50000:
            body = body[:50000]
        pub_parts = sel.css(".publish-time::text, .meta::text, time::text").getall()
        pub_s = " ".join(p.strip() for p in pub_parts if p and p.strip())
        article_source = (sel.css(".article-source::text").get() or "").strip()
        kw_raw = (sel.css('meta[name="keywords"]::attr(content)').get() or "").strip()
        html_keywords: list[str] = []
        for part in kw_raw.replace("，", ",").split(","):
            k = part.strip()
            if k and k not in html_keywords:
                html_keywords.append(k)
        return {
            "title": title,
            "body": body,
            "publish_time_str": pub_s,
            "page_category": "",
            "article_source": article_source,
            "html_keywords": html_keywords[:16],
        }
