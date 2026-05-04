from __future__ import annotations

import re
import sys
from urllib.parse import urljoin, urlparse

from parsel import Selector
from scrapy import Request, Spider

from ..normalizer import clean_text_encoding_guard, looks_like_mojibake

# 从原始 HTML 文本中提取 href（不依赖 DOM 树，避免中途 </html> 截断导致 parsel 只见头部）
_GOV_HREF_RE = re.compile(
    r"""href\s*=\s*(['"])([^"'<>]*)\1|href\s*=\s*([^\s>"']+)""",
    re.IGNORECASE,
)


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

    v1.4.2：gov.cn /zhengce/ 列表在原始 HTML 上做正则 href 回退；unwrap 早闭 </html> 后再解析；
    详情正文仅从正文容器抽取，并检测 CSS/JS/nav 等污染后 skip。
    v1.4.3：gov 详情拆 full_sel（标题/meta/时间/来源）与 content_sel（仅正文）；列表 Request.meta link_text 标题兜底。
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
        # gov.cn 列表：详情 URL -> 列表页 <a> 文本（正则回退无锚文本）
        self._link_text_by_url: dict[str, str] = {}

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

    @staticmethod
    def _is_gov_zhengce_list_url(url: str) -> bool:
        u = (url or "").lower()
        host = (urlparse(u).hostname or "").lower()
        return "gov.cn" in host and "zhengce" in u

    @staticmethod
    def _gov_regex_hrefs(html: str) -> list[str]:
        out: list[str] = []
        for m in _GOV_HREF_RE.finditer(html or ""):
            g2 = m.group(2)
            g3 = m.group(3)
            h = (g2 if g2 is not None else g3 or "").strip()
            if h:
                out.append(h)
        return out

    @staticmethod
    def _gov_unwrap_after_false_html_close(html: str) -> str:
        """
        部分 gov 页在头部后插入假的 </html>，lxml/parsel 只解析到头部。
        若 </html> 之后仍有大量含 zhengce/href 的正文片段，则丢弃该闭标签之前的前缀。
        """
        m = re.search(r"(?is)</html>\s*", html)
        if not m:
            return html
        tail = html[m.end() :]
        if len(tail) < 400:
            return html
        tl = tail.lower()
        if "/zhengce" in tl or ("href" in tl and ("content_" in tl or ".htm" in tl or ".shtml" in tl)):
            return tail.lstrip()
        return html

    @staticmethod
    def _gov_prepare_html_for_parse(html: str, page_url: str) -> str:
        if not StaticNewsSpider._is_gov_zhengce_list_url(page_url) and not StaticNewsSpider._is_gov_zhengce_policy_url(
            page_url
        ):
            return html
        return StaticNewsSpider._gov_unwrap_after_false_html_close(html)

    @staticmethod
    def _is_gov_zhengce_list_root_url(url: str) -> bool:
        """
        政策频道「壳」列表（非单篇正文 URL）：避免对列表页误用详情正文切片。
        """
        u = urlparse(url or "")
        if "gov.cn" not in (u.netloc or "").lower() or "zhengce" not in (url or "").lower():
            return False
        segs = [s for s in (u.path or "").split("/") if s]
        if not segs:
            return True
        if len(segs) == 1 and segs[0].lower() == "zhengce":
            return True
        last = segs[-1].lower()
        if "." in last and last.endswith((".htm", ".html", ".shtml")):
            return False
        return True

    @staticmethod
    def _gov_detail_content_fragment_html(html: str) -> str:
        """
        详情页：在已 unwrap 的全文 html 上，从正文容器起始切片（仅用于正文 selector，不用于 title/meta）。
        """
        m = re.search(
            r"(?is)<div[^>]*\bid\s*=\s*['\"]UCAP-CONTENT['\"][^>]*>|"
            r"<div[^>]*\bclass\s*=\s*['\"][^'\"]*pages_content[^'\"]*['\"][^>]*>|"
            r"<div[^>]*\bclass\s*=\s*['\"][^'\"]*article-content[^'\"]*['\"][^>]*>",
            html,
        )
        if m:
            return html[m.start() :]
        return html

    def _gov_detail_full_and_content_selectors(self, response) -> tuple[Selector, Selector]:
        raw = response.body.decode("utf-8", errors="replace")
        full_html = self._gov_unwrap_after_false_html_close(raw)
        content_html = self._gov_detail_content_fragment_html(full_html)
        return Selector(text=full_html), Selector(text=content_html)

    def _decoded_selector(self, response):
        """
        返回 (parsel.Selector, used_encoding_label)。
        本机：UTF-8 严格解码 body + Selector(text=html) -> utf-8-forced。
        gov.cn /zhengce：utf-8 replace + unwrap 假 </html> 后再 Selector（列表与详情）。
        其它远端：沿用 Scrapy 的 response.selector 与自动 encoding。
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

        if "gov.cn" in host and (
            self._is_gov_zhengce_list_url(response.url) or self._is_gov_zhengce_policy_url(response.url)
        ):
            raw = response.body.decode("utf-8", errors="replace")
            if self._is_gov_zhengce_list_root_url(response.url):
                prep = self._gov_prepare_html_for_parse(raw, response.url)
            else:
                prep = self._gov_detail_content_fragment_html(raw)
            sel = Selector(text=prep)
            used = "utf-8-replace+gov_html_prepare"
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
        raw_html = response.body.decode("utf-8", errors="replace")
        sel, _used_enc = self._decoded_selector(response)
        mode = self._detect_list_mode(response)
        ah_css = sel.css("a::attr(href)").getall() or []

        if mode == "gov_zhengce":
            ah_re = self._gov_regex_hrefs(raw_html)
            all_hrefs = self._gov_merge_href_strings(ah_css + ah_re)
            links_sel = self._links_gov_policy(sel, response.url)
            links_re = self._links_gov_policy_from_raw_hrefs(ah_re, response.url)
            links = self._merge_gov_policy_link_pairs(links_sel, links_re)
            self._log_gov_zhengce_list_diagnostics(response, sel, all_hrefs, links, len(ah_css), len(ah_re))
        elif mode == "demo_list":
            all_hrefs = ah_css
            links = self._links_demo_list(sel, response.url)
        else:
            all_hrefs = ah_css
            links = self._links_generic(sel, response.url)

        if not links:
            if mode == "generic":
                rec = self._record_from_detail(response, sel)
                if rec:
                    self._append_record(rec)
            return

        if mode == "gov_zhengce":
            for href, link_text in links:
                if len(self.collector) >= self._detail_goal:
                    break
                self._link_text_by_url[href] = (link_text or "").strip()
                yield Request(
                    href,
                    callback=self.parse_detail,
                    errback=self._err,
                    meta={"link_text": self._link_text_by_url.get(href, "")},
                )
            return

        for href in links:
            if len(self.collector) >= self._detail_goal:
                break
            yield response.follow(href, callback=self.parse_detail, errback=self._err)

    @staticmethod
    def _gov_merge_href_strings(hrefs: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for h in hrefs:
            key = (h or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(key)
        return out

    @staticmethod
    def _merge_gov_policy_link_pairs(
        first: list[tuple[str, str]], second: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        seen: set[str] = set()
        out: list[tuple[str, str]] = []
        for url, text in first + second:
            if not url or url in seen:
                continue
            seen.add(url)
            out.append((url, (text or "").strip()))
        return out

    def parse_detail(self, response):
        url = response.url or ""
        if self._is_gov_zhengce_policy_url(url) and not self._is_gov_zhengce_list_root_url(url):
            full_sel, content_sel = self._gov_detail_full_and_content_selectors(response)
            rec = self._record_from_detail(response, content_sel, full_sel=full_sel)
        else:
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
        self,
        response,
        sel: Selector,
        all_hrefs: list[str],
        links: list[tuple[str, str]],
        selector_href_count: int,
        regex_href_raw_count: int,
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
            f"  selector_a_href_count={selector_href_count}\n"
            f"  regex_href_raw_count={regex_href_raw_count}\n"
            f"  a_href_merged_unique={len(all_hrefs)}\n"
            f"  href_preview_first20={raw_preview!r}\n"
            f"  detail_links_count={len(links)}\n"
            f"  detail_links_first10={[u for u, _ in links[:10]]!r}\n"
        )
        if not links:
            msg += "  reason: gov.cn list page reached but no detail links extracted\n"
        print(msg, file=sys.stderr, flush=True)

    def _log_gov_detail_skip(self, url: str, body_len: int, reason: str) -> None:
        print(
            f"[gov.cn zhengce detail skip] url={url!r} reason={reason!r} body_len={body_len}\n",
            file=sys.stderr,
            flush=True,
        )

    def _log_gov_title_empty_debug(
        self,
        url: str,
        candidates: dict[str, str],
        body_len: int,
        body_sample: str,
    ) -> None:
        print(
            "[gov.cn zhengce detail title_empty_debug]\n"
            f"  url={url!r}\n"
            f"  title_candidates={candidates!r}\n"
            f"  body_len={body_len}\n"
            f"  body_sample={body_sample[:80]!r}\n",
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

    def _gov_href_invalid(self, full: str) -> bool:
        low = full.lower()
        p = urlparse(full)
        net = (p.netloc or "").lower()
        path = (p.path or "").lower()

        if "english." in net or net.startswith("english."):
            return True
        if "big5" in low or "/gate/big5/" in path:
            return True
        if "mail." in net or "mailto:" in low or "/nsmail" in path:
            return True
        if "login" in path or "/reg" in path or "register" in path:
            return True
        for ext in (".js", ".css", ".json", ".xml", ".pdf", ".zip", ".jpg", ".png", ".gif", ".ico", ".woff"):
            if low.endswith(ext) or ext + "?" in low:
                return True
        if "javascript:" in low:
            return True
        return False

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

    def _gov_normalize_policy_url(self, href: str, page_url: str) -> str | None:
        h = (href or "").strip()
        if not h or h.startswith("#"):
            return None
        full = urljoin(page_url, h.split("#")[0])
        if full.startswith("//"):
            full = "https:" + full
        low = full.lower()
        if not full.startswith("http"):
            return None
        if "javascript:" in low or "mailto:" in low:
            return None
        if self._gov_href_invalid(full):
            return None
        if "gov.cn" not in urlparse(full).netloc.lower():
            return None
        path = urlparse(full).path.lower()
        pn = path.rstrip("/")
        if not (path.startswith("/zhengce/") or pn == "/zhengce"):
            return None
        if not low.endswith((".htm", ".html", ".shtml")):
            return None
        if self._gov_policy_link_excluded(full, page_url):
            return None
        return full

    def _links_gov_policy(self, sel: Selector, page_url: str) -> list[tuple[str, str]]:
        """
        gov.cn + 路径含 /zhengce/ + 常见正文后缀；不强制 content_；去重保序。
        返回 (url, anchor_text)；锚文本来自同一 <a> 节点 ::text。
        """
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for node in sel.css("a"):
            href = node.css("::attr(href)").get()
            parts = [x.strip() for x in (node.css("::text").getall() or []) if x and x.strip()]
            anchor = " ".join(parts).strip()
            full = self._gov_normalize_policy_url((href or "").strip(), page_url)
            if not full or full in seen:
                continue
            seen.add(full)
            out.append((full, anchor))
            if len(out) >= self._detail_goal:
                break
        return out[: self._detail_goal]

    def _links_gov_policy_from_raw_hrefs(self, raw_hrefs: list[str], page_url: str) -> list[tuple[str, str]]:
        """源码级 href 列表（正则无锚文本），再经统一归一化与过滤。"""
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for href in raw_hrefs:
            full = self._gov_normalize_policy_url(href, page_url)
            if not full or full in seen:
                continue
            seen.add(full)
            out.append((full, ""))
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

    def _gov_body_polluted(self, body: str) -> tuple[bool, str]:
        if not body:
            return True, "empty_body"
        low = body.lower()
        # 明显脚本 / 样式 / 导航残留
        if "<script" in low or "</script>" in low:
            return True, "contains_script_tag_fragment"
        if re.search(r"\bfunction\s*\(", low) and low.count("{") > 8:
            return True, "looks_like_minified_js"
        if "@media" in low or "@import" in low or "stylesheet" in low:
            return True, "contains_css_keywords"
        if "window.location" in low or "document.cookie" in low:
            return True, "contains_dom_js_api"
        # 导航/页脚常见英文块（正文政策页不应大量出现）
        nav_hits = sum(1 for k in (" header ", " footer ", " navbar", "breadcrumb", " nav ") if k in low)
        if nav_hits >= 3 and len(body) < 800:
            return True, "nav_like_keywords_dense"
        return False, ""

    def _record_from_detail(self, response, sel: Selector, full_sel: Selector | None = None) -> dict | None:
        url = response.url or ""
        if url in self._seen_detail:
            return None

        is_gov_detail = self._is_gov_zhengce_policy_url(url) and not self._is_gov_zhengce_list_root_url(url)
        mode = "gov" if is_gov_detail else "generic"

        if mode == "gov":
            fs = full_sel if full_sel is not None else sel
            link_text = (getattr(response, "meta", None) or {}).get("link_text") or ""
            link_text = str(link_text).strip()
            ex = self._extract_gov(content_sel=sel, full_sel=fs, link_text=link_text)
        else:
            ex = self._extract_generic(sel)

        title = (ex.get("title") or "").strip()
        body = (ex.get("body") or "").strip()

        if mode == "gov":
            bad, p_reason = self._gov_body_polluted(body)
            if bad:
                self._log_gov_detail_skip(url, len(body), f"polluted:{p_reason}")
                return None
            if not title:
                cand = ex.get("_title_candidates") or {}
                self._log_gov_title_empty_debug(url, cand, len(body), body)
                self._log_gov_detail_skip(url, len(body), "title_empty")
                return None
            if len(body) < 8:
                self._log_gov_detail_skip(url, len(body), "body_too_short")
                return None
        else:
            if not title or len(body) < 8:
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

    @staticmethod
    def _gov_clean_title(title: str) -> str:
        t = (title or "").strip()
        if not t:
            return ""
        suffixes = ("__中国政府网", "_中国政府网", "- 中国政府网", "中国政府网")
        changed = True
        while changed and t:
            changed = False
            for suf in suffixes:
                if t.endswith(suf):
                    t = t[: -len(suf)].strip()
                    changed = True
        return t.strip()

    def _extract_gov(self, content_sel: Selector, full_sel: Selector, link_text: str = "") -> dict:
        c = content_sel
        f = full_sel
        lt_raw = (link_text or "").strip()

        def _t(x: str | None) -> str:
            return self._gov_clean_title((x or "").strip())

        h1_c = _t(c.css("h1::text").get())
        h1_f = _t(f.css("h1::text").get())
        at_f = _t(f.css(".article-title::text").get())
        og = _t(f.css('meta[property="og:title"]::attr(content)').get())
        art_title = _t(f.css('meta[name="ArticleTitle"]::attr(content)').get())
        meta_title = _t(f.css('meta[name="title"]::attr(content)').get())
        page_title = _t(f.css("title::text").get())
        lt = _t(lt_raw)

        title = self._gov_clean_title(h1_c or h1_f or at_f or og or art_title or meta_title or page_title or lt)

        candidates = {
            "h1_content": h1_c,
            "h1_full": h1_f,
            "article_title_class": at_f,
            "meta_og_title": og,
            "meta_article_title": art_title,
            "meta_name_title": meta_title,
            "page_title": page_title,
            "link_text": lt,
        }

        # 正文仅从正文容器（content_sel）抽取
        body_chunks: list[str] = []
        for css in (
            "#UCAP-CONTENT *::text",
            ".pages_content *::text",
            ".article-content *::text",
        ):
            parts = c.css(css).getall() or []
            chunk = "\n".join(p.strip() for p in parts if p and p.strip())
            if chunk:
                body_chunks.append(chunk)
        body = "\n\n".join(body_chunks)
        if len(body) > 50000:
            body = body[:50000]

        pub_s = (
            (f.css(".pages-date::text").get() or "").strip()
            or (f.css(".time::text").get() or "").strip()
            or (f.css("#docData time::text").get() or "").strip()
            or (f.css('meta[name="PubDate"]::attr(content)').get() or "").strip()
        )
        if not pub_s:
            blob = " ".join(
                (c.css("#UCAP-CONTENT *::text, .pages_content *::text, .article-content *::text").getall() or [])[
                    :400
                ]
            )
            m = re.search(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", blob[:8000])
            if m:
                pub_s = m.group(0).strip()

        article_source = (f.css(".source::text").get() or "").strip() or (f.css(".pages-source::text").get() or "").strip()
        if not article_source:
            for line in (c.css("#UCAP-CONTENT *::text, .pages_content *::text").getall() or [])[:120]:
                t = (line or "").strip()
                if "来源：" in t or "来源:" in t:
                    article_source = t[:300]
                    break

        crumbs = f.css(".breadcrumb a::text, .BreadcrumbNav a::text").getall()
        cat = " > ".join(x.strip() for x in crumbs if x.strip())[:200]

        return {
            "title": title,
            "body": body,
            "publish_time_str": pub_s,
            "page_category": cat,
            "article_source": article_source,
            "html_keywords": [],
            "_title_candidates": candidates,
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
