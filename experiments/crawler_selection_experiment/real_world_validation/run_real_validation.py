from __future__ import annotations

import csv
import json
import random
import re
import ssl
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = Path("experiments/crawler_selection_experiment")
LOCAL_CONFIG = BASE_DIR / "real_world_validation" / "validation_sources.local.json"
EXAMPLE_CONFIG = BASE_DIR / "real_world_validation" / "validation_sources.example.json"

STAGE2_OUT_DIR = BASE_DIR / "results" / "stage2_real_world"

# Stage2 统一字段集合（用于 completeness 统计与输出对齐）。
ALL_FIELDS = ["title", "content", "source", "source_url", "publish_time", "category", "keywords"]

# 默认 required_fields（大多数源仍要求 publish_time；但动态栏目型页面可单独放宽）
DEFAULT_REQUIRED_FIELDS = list(ALL_FIELDS)


@dataclass
class ValidationRow:
    source_name: str
    region: str
    scenario: str
    url: str
    collector: str
    robots_allowed: str
    robots_url: str
    robots_error_type: str
    robots_error_message: str
    status: str
    item_count: int
    valid_count: int
    field_completeness: float
    elapsed_seconds: float
    error_message: str
    validation_conclusion: str
    http_status_code: str
    content_type: str
    response_length: str
    final_url: str
    feed_title: str
    entries_count: str
    bozo: str
    bozo_exception: str


@dataclass
class ItemRow:
    source_name: str
    scenario: str
    collector: str
    item_index: int
    title: str
    content: str
    source: str
    source_url: str
    publish_time: str
    category: str
    keywords: List[str]
    is_valid: bool
    missing_fields: List[str]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: List[ValidationRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))


def _write_json(path: Path, rows: List[ValidationRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2), encoding="utf-8")


def _write_items_json(path: Path, rows: List[ItemRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2), encoding="utf-8")


def _write_items_csv(path: Path, rows: List[ItemRow]) -> None:
    """
    CSV 用 utf-8-sig，便于 Excel 打开不乱码。
    keywords/missing_fields 写为 JSON 字符串，方便后续解析。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            d = asdict(r)
            d["keywords"] = json.dumps(d.get("keywords") or [], ensure_ascii=False)
            d["missing_fields"] = json.dumps(d.get("missing_fields") or [], ensure_ascii=False)
            w.writerow(d)


def _fetch(url: str, timeout: float = 15.0) -> Tuple[int, str, str, int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FACT-crawler-selection-experiment/1.0 (public validation; respect robots.txt)",
        },
        method="GET",
    )
    # use explicit SSL context for more stable diagnostics on some hosts
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        content_type = str(resp.headers.get("Content-Type") or "")
        final_url = str(getattr(resp, "geturl", lambda: url)())
        raw = resp.read()
        text = raw.decode(charset, errors="replace")
        return int(getattr(resp, "status", 200)), text, content_type, len(raw), final_url


def _robots_status(url: str, user_agent: str = "*") -> Tuple[str, str, str, str, str]:
    """
    返回 (robots_allowed, robots_url, robots_error_type, robots_error_message, detail)

    - "allowed": robots 明确允许抓取该 URL
    - "disallowed": robots 明确禁止抓取该 URL
    - "unknown": robots 无法确认（robots.txt 不可达/解析失败/URL 非法）
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return "unknown", "", "ValueError", "invalid url", "invalid url"
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception as e:
            return "unknown", robots_url, type(e).__name__, str(e), f"robots fetch failed: {e} ({robots_url})"
        allowed = bool(rp.can_fetch(user_agent, url))
        return ("allowed" if allowed else "disallowed"), robots_url, "", "", f"robots={robots_url}"
    except Exception as e:
        return "unknown", "", type(e).__name__, str(e), f"robots check failed: {e}"


def _field_ok(f: str, v: Any) -> bool:
    if f == "keywords":
        return isinstance(v, list) and len(v) > 0
    return v is not None and v != ""


def _missing_fields_for_item(it: dict, required_fields: List[str]) -> List[str]:
    missing: List[str] = []
    for f in required_fields:
        if not _field_ok(f, it.get(f)):
            missing.append(f)
    return missing


def _compute_valid_and_completeness(items: List[dict], required_fields: List[str], completeness_fields: List[str]) -> Tuple[int, float]:
    """
    valid_count：按 required_fields 判定（每条 item 所有 required_fields 都满足才算 valid）
    field_completeness：按 completeness_fields 统计（用于“整体字段质量”观测）
    """
    if not items:
        return 0, 0.0
    total = 0
    ok = 0
    valid = 0
    for it in items:
        item_ok = True
        for f in completeness_fields:
            total += 1
            ok += 1 if _field_ok(f, it.get(f)) else 0
        for f in required_fields:
            if not _field_ok(f, it.get(f)):
                item_ok = False
                break
        if item_ok:
            valid += 1
    return valid, (ok / total if total else 0.0)


def _sleep_1_3s() -> None:
    time.sleep(random.uniform(1.0, 3.0))


def _strip_tags(s: str) -> str:
    s = re.sub(r"(?is)<script.*?>.*?</script>", " ", s)
    s = re.sub(r"(?is)<style.*?>.*?</style>", " ", s)
    s = re.sub(r"(?is)<.*?>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _extract_links(html: str) -> List[str]:
    # very small, dependency-free href extraction
    links: List[str] = []
    for m in re.finditer(r'(?is)\bhref\s*=\s*["\']([^"\']+)["\']', html):
        href = (m.group(1) or "").strip()
        if not href or href.startswith("#"):
            continue
        links.append(href)
    return links


def _first_match(text: str, patterns: List[str]) -> str:
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return (m.group(1) or "").strip()
    return ""


def _keywords_simple(text: str, base: Optional[List[str]] = None, limit: int = 8) -> List[str]:
    base = base or []
    # keep short chinese/word tokens; remove very common particles
    raw = re.findall(r"[\u4e00-\u9fff]{2,6}|[A-Za-z]{3,12}", text or "")
    stop = {"关于", "有关", "通知", "公告", "意见", "办法", "规定", "实施", "工作", "方案"}
    out: List[str] = []
    for t in base + raw:
        t = t.strip()
        if not t or t in stop:
            continue
        if t not in out:
            out.append(t)
        if len(out) >= limit:
            break
    return out


def _parse_gov_policy_static_list(list_url: str, html: str, max_items: int) -> List[str]:
    # gov.cn policy list commonly links to /zhengce/content/xxxxxx.htm
    links = _extract_links(html)
    abs_links: List[str] = []
    for href in links:
        u = urllib.parse.urljoin(list_url, href)
        if "www.gov.cn" not in urllib.parse.urlparse(u).netloc:
            continue
        if "/zhengce/content/" in u and u.lower().endswith((".htm", ".html")):
            if u not in abs_links:
                abs_links.append(u)
        if len(abs_links) >= max_items:
            break
    return abs_links[:max_items]


def _parse_gov_policy_detail(url: str, html: str) -> dict:
    title = _first_match(
        html,
        [
            r"(?is)<h1[^>]*>(.*?)</h1>",
            r"(?is)<title[^>]*>(.*?)</title>",
        ],
    )
    title = _strip_tags(title)
    publish_time = _first_match(
        html,
        [
            r"(?is)<time[^>]*>(.*?)</time>",
            r"(?is)发布时间[:：]?\s*([0-9]{4}[-/\.][0-9]{1,2}[-/\.][0-9]{1,2})",
            r"(?is)([0-9]{4}[-/\.][0-9]{1,2}[-/\.][0-9]{1,2})",
        ],
    )
    publish_time = _strip_tags(publish_time)

    text = _strip_tags(html)
    snippet = text[:600]

    source = "中国政府网"
    content = f"{title}\n来源：{source}\n时间：{publish_time}\n摘要：{snippet}"
    return {
        "title": title,
        "content": content,
        "source": source,
        "source_url": url,
        "publish_time": publish_time,
        "category": "gov_policy",
        "keywords": _keywords_simple(title, base=["政策", "国务院"], limit=8),
    }


def _parse_chinadaily_rss(url: str, max_items: int) -> List[dict]:
    raise RuntimeError("deprecated: use _validate_rss_feedparser() for diagnostics")


def _looks_like_html(content_type: str, body: str) -> bool:
    ct = (content_type or "").lower()
    head = (body or "")[:200].lstrip().lower()
    if "text/html" in ct:
        return True
    return head.startswith("<!doctype html") or head.startswith("<html") or "<html" in head


def _summarize_head(body: str, n: int = 100) -> str:
    s = _strip_tags((body or "")[:500])
    return s[:n]


def _validate_rss_feedparser(url: str, max_items: int, source_label: str) -> Tuple[List[dict], Dict[str, str]]:
    """
    RSS 诊断增强：
    - 先抓取 URL 记录 http_status_code/content_type/response_length/final_url
    - 再 feedparser.parse(body) 记录 feed_title/entries_count/bozo/bozo_exception
    """
    diag: Dict[str, str] = {
        "http_status_code": "",
        "content_type": "",
        "response_length": "",
        "final_url": "",
        "feed_title": "",
        "entries_count": "",
        "bozo": "",
        "bozo_exception": "",
    }

    try:
        import feedparser  # type: ignore
    except Exception as e:
        raise RuntimeError(f"feedparser import failed: {type(e).__name__}: {e}")

    try:
        sc, body, ct, ln, final_url = _fetch(url)
        diag["http_status_code"] = str(sc)
        diag["content_type"] = ct
        diag["response_length"] = str(ln)
        diag["final_url"] = final_url
        if sc >= 400:
            raise RuntimeError(f"http {sc}; content_type={ct}; response_length={ln}; final_url={final_url}")
        if _looks_like_html(ct, body):
            head = _summarize_head(body, n=100)
            raise RuntimeError(f"RSS returned HTML; content_type={ct}; head={head}")
    except Exception as e:
        raise RuntimeError(f"RSS HTTP fetch failed: {type(e).__name__}: {e}")

    d = feedparser.parse(body)
    feed_title = (getattr(getattr(d, "feed", None), "title", "") or "").strip()
    entries = list(getattr(d, "entries", None) or [])
    bozo = bool(getattr(d, "bozo", False))
    bozo_exc = getattr(d, "bozo_exception", None)

    diag["feed_title"] = feed_title
    diag["entries_count"] = str(len(entries))
    diag["bozo"] = "1" if bozo else "0"
    diag["bozo_exception"] = (repr(bozo_exc) if bozo_exc is not None else "")

    if len(entries) == 0:
        raise RuntimeError(
            "feedparser entries_count=0; "
            f"bozo={diag['bozo']}; bozo_exception={diag['bozo_exception']}; "
            f"content_type={diag['content_type']}; response_length={diag['response_length']}; final_url={diag['final_url']}"
        )

    items: List[dict] = []
    for e in entries[:max_items]:
        title = (getattr(e, "title", "") or "").strip()
        summary = (getattr(e, "summary", "") or getattr(e, "description", "") or "").strip()
        link = (getattr(e, "link", "") or "").strip() or url
        published = (getattr(e, "published", "") or getattr(e, "updated", "") or "").strip()
        items.append(
            {
                "title": title,
                "content": summary,
                "source": source_label,
                "source_url": link,
                "publish_time": published,
                "category": "china_news / rss_news",
                "keywords": _keywords_simple(f"{title} {summary}", base=["中国", "要闻"], limit=10),
            }
        )
    return items, diag


def _is_nbs_invalid_text(t: str) -> bool:
    """
    nbs_data_dynamic 专用：过滤页脚/备案/登录注册等非业务入口文本。
    """
    bad_kw = (
        "京公网安备",
        "京ICP备",
        "ICP备",
        "ICP",
        "备案",
        "公安",
        "版权所有",
        "网站地图",
        "联系我们",
        "登录",
        "注册",
        "帮助",
    )
    if any(k in t for k in bad_kw):
        return True

    # 正则：包含备案/安备
    if re.search(r"(公网安备|ICP备)", t):
        return True

    # 正则：页脚编号类（主要由数字/字母/符号 + 备案类词组成）
    # 示例：京公网安备 11040102700142号 / 京ICP备05034670号-2
    compact = re.sub(r"\s+", "", t)
    if len(compact) >= 8:
        # 先判定“像备案串”：含号、-、或大量数字
        looks_like_id = bool(re.search(r"[0-9]{6,}", compact)) and bool(re.search(r"(号|[-_])", compact))
        # 若文本中汉字极少且包含编号特征，则视为页脚类
        han_count = len(re.findall(r"[\u4e00-\u9fff]", compact))
        if looks_like_id and han_count <= 6:
            return True

    return False


def _pick_text_blocks(texts: List[str], max_items: int, *, nbs_strict_filter: bool = False) -> List[str]:
    """
    对可见文本做去重与关键词优先排序。
    """
    kw = ("数据", "年度", "分省", "城市", "部门", "统计", "指标")
    seen = set()
    cleaned: List[str] = []
    for t in texts:
        t = re.sub(r"\s+", " ", (t or "")).strip()
        if not t:
            continue
        if len(t) < 2:
            continue
        if nbs_strict_filter and _is_nbs_invalid_text(t):
            continue
        if len(t) > 60:
            t = t[:60]
        if t in seen:
            continue
        seen.add(t)
        cleaned.append(t)

    def score(t: str) -> Tuple[int, int]:
        hit = sum(1 for k in kw if k in t)
        return (hit, len(t))

    cleaned.sort(key=lambda x: score(x), reverse=True)
    picked: List[str] = []
    for t in cleaned:
        if any(k in t for k in kw):
            picked.append(t)
        if len(picked) >= max_items:
            return picked[:max_items]
    for t in cleaned:
        if t not in picked:
            picked.append(t)
        if len(picked) >= max_items:
            break
    return picked[:max_items]


def _validate_nbs_data_dynamic(url: str, max_items: int) -> Tuple[List[dict], Dict[str, str]]:
    """
    国家统计局国家数据平台：JS 渲染页面，使用 Playwright 渲染后抽取可见菜单/链接/按钮文本。
    返回 (items, diag)
    """
    diag: Dict[str, str] = {
        "http_status_code": "",
        "content_type": "",
        "final_url": "",
        "rendered_html_length": "",
        "detected_links_count": "",
        "detected_text_blocks_count": "",
        "page_title": "",
        "text_head_200": "",
    }

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as e:
        raise RuntimeError(f"playwright import failed: {type(e).__name__}: {e}")

    items: List[dict] = []
    source = "国家统计局国家数据平台"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_load_state("networkidle", timeout=45000)
        time.sleep(random.uniform(2.0, 3.0))

        diag["final_url"] = page.url or url
        if resp is not None:
            try:
                diag["http_status_code"] = str(resp.status)
            except Exception:
                diag["http_status_code"] = ""
            try:
                diag["content_type"] = str(resp.headers.get("content-type") or "")
            except Exception:
                diag["content_type"] = ""

        page_title = page.title() or ""
        diag["page_title"] = page_title

        html = page.content() or ""
        diag["rendered_html_length"] = str(len(html))

        js = """
        () => {
          const nodes = Array.from(document.querySelectorAll(
            'a, button, [role="menuitem"], [role="button"], nav a, li, .card, .menu'
          ));
          const out = [];
          for (const el of nodes) {
            const txt = (el.innerText || el.textContent || '').replace(/\\s+/g,' ').trim();
            if (!txt) continue;
            const rect = el.getBoundingClientRect();
            const visible = rect.width > 0 && rect.height > 0;
            if (!visible) continue;
            let href = '';
            if (el.tagName && el.tagName.toLowerCase() === 'a') {
              href = el.getAttribute('href') || '';
            } else {
              const a = el.closest('a');
              if (a) href = a.getAttribute('href') || '';
            }
            out.push({text: txt, href});
          }
          return out;
        }
        """
        blocks = page.evaluate(js) or []
        diag["detected_text_blocks_count"] = str(len(blocks))

        texts: List[str] = []
        hrefs: List[str] = []
        for b in blocks:
            if not isinstance(b, dict):
                continue
            texts.append(str(b.get("text") or ""))
            hrefs.append(str(b.get("href") or ""))
        diag["detected_links_count"] = str(sum(1 for h in hrefs if h))

        picked = _pick_text_blocks(texts, max_items=max_items, nbs_strict_filter=True)

        body_text = _strip_tags(html)
        diag["text_head_200"] = (body_text[:200] if body_text else "")

        for t in picked:
            content = f"{t}\n页面标题：{page_title}\n栏目说明：国家数据平台（JS 渲染）"
            items.append(
                {
                    "title": t,
                    "content": content,
                    "source": source,
                    "source_url": url,
                    "publish_time": "",
                    "category": "statistics_dynamic",
                    "keywords": _keywords_simple(f"{t} {content}", base=["国家数据", "统计", "年度数据"], limit=10),
                }
            )

        context.close()
        browser.close()

    return items, diag


def _parse_policy_library_dynamic_minimal(url: str, html: str, max_items: int) -> List[dict]:
    """
    MVP：尽量在“无需登录/不绕反爬”的前提下，从可见 HTML 中提取少量候选链接/标题。
    若页面完全依赖 JS 且无可见数据，则返回空列表，提示需要补充解析规则（或在合规前提下定位 XHR 接口）。
    """
    text = _strip_tags(html)
    # try to find any policy-related detail links
    links = _extract_links(html)
    detail_links: List[str] = []
    for href in links:
        u = urllib.parse.urljoin(url, href)
        if "www.gov.cn" not in urllib.parse.urlparse(u).netloc:
            continue
        if u.lower().endswith((".htm", ".html")) and u not in detail_links:
            detail_links.append(u)
        if len(detail_links) >= max_items:
            break

    items: List[dict] = []
    source = "中国政府网政策文件库"
    if detail_links:
        # treat as list-to-detail; only validate minimum fields
        for u in detail_links[:max_items]:
            items.append(
                {
                    "title": u.split("/")[-1],
                    "content": f"详情页 URL：{u}\n列表页片段：{text[:300]}",
                    "source": source,
                    "source_url": u,
                    "publish_time": "",
                    "category": "gov_policy_dynamic",
                    "keywords": _keywords_simple(text[:200], base=["政策", "文件库"], limit=8),
                }
            )
    return items


def _validate_one(scenario: str, src: dict) -> ValidationRow:
    name = str(src.get("name") or "")
    region = str(src.get("region") or "")
    url = str(src.get("url") or "")
    collector = str(src.get("collector") or "")
    max_items = int(src.get("max_items") or 0) or 10

    # 合规提示（记录到结论中，避免静默抓取）
    compliance_note = "no-login/no-captcha/no-bypass/no-PII + respect robots + rate-limit"

    if not url or not collector:
        return ValidationRow(
            source_name=name or "(missing)",
            region=region,
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed="unknown",
            robots_url="",
            robots_error_type="",
            robots_error_message="",
            status="skipped",
            item_count=0,
            valid_count=0,
            field_completeness=0.0,
            elapsed_seconds=0.0,
            error_message="missing url or collector",
            validation_conclusion=f"skipped: invalid config ({compliance_note})",
            http_status_code="",
            content_type="",
            response_length="",
            final_url="",
            feed_title="",
            entries_count="",
            bozo="",
            bozo_exception="",
        )

    robots_allowed, robots_url, robots_err_type, robots_err_msg, robots_detail = _robots_status(url)
    if robots_allowed == "disallowed":
        return ValidationRow(
            source_name=name,
            region=region,
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed=robots_allowed,
            robots_url=robots_url,
            robots_error_type=robots_err_type,
            robots_error_message=robots_err_msg,
            status="skipped",
            item_count=0,
            valid_count=0,
            field_completeness=0.0,
            elapsed_seconds=0.0,
            error_message=robots_detail,
            validation_conclusion="合规原因跳过（robots 明确不允许）",
            http_status_code="",
            content_type="",
            response_length="",
            final_url="",
            feed_title="",
            entries_count="",
            bozo="",
            bozo_exception="",
        )

    if robots_allowed == "unknown":
        return ValidationRow(
            source_name=name,
            region=region,
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed=robots_allowed,
            robots_url=robots_url,
            robots_error_type=robots_err_type,
            robots_error_message=robots_err_msg,
            status="robots_unknown",
            item_count=0,
            valid_count=0,
            field_completeness=0.0,
            elapsed_seconds=0.0,
            error_message=robots_detail,
            validation_conclusion="robots 获取失败，按合规策略未执行正式采集；该结果不计为采集技术失败。",
            http_status_code="",
            content_type="",
            response_length="",
            final_url="",
            feed_title="",
            entries_count="",
            bozo="",
            bozo_exception="",
        )

    start = time.perf_counter()
    try:
        items: List[dict] = []
        body: str = ""
        http_status_code = ""
        content_type = ""
        response_length = ""
        final_url = ""
        feed_title = ""
        entries_count = ""
        bozo = ""
        bozo_exception = ""
        rendered_html_length = ""
        detected_links_count = ""
        detected_text_blocks_count = ""
        page_title = ""
        text_head_200 = ""

        # RSS：诊断增强（贴近第一阶段选型：feedparser）
        if scenario == "rss_api" and collector == "feedparser_rss_api":
            source_label = "中国日报 RSS" if name == "china_daily_china_rss" else "中国新闻网 RSS"
            items, diag = _validate_rss_feedparser(url, max_items=max_items, source_label=source_label)
            http_status_code = diag.get("http_status_code", "")
            content_type = diag.get("content_type", "")
            response_length = diag.get("response_length", "")
            final_url = diag.get("final_url", "")
            feed_title = diag.get("feed_title", "")
            entries_count = diag.get("entries_count", "")
            bozo = diag.get("bozo", "")
            bozo_exception = diag.get("bozo_exception", "")
        elif scenario == "dynamic_page" and name == "nbs_data_dynamic" and collector == "scrapy_playwright_dynamic":
            items, d2 = _validate_nbs_data_dynamic(url, max_items=max_items)
            http_status_code = d2.get("http_status_code", "")
            content_type = d2.get("content_type", "")
            final_url = d2.get("final_url", "") or url
            rendered_html_length = d2.get("rendered_html_length", "")
            detected_links_count = d2.get("detected_links_count", "")
            detected_text_blocks_count = d2.get("detected_text_blocks_count", "")
            page_title = d2.get("page_title", "")
            text_head_200 = d2.get("text_head_200", "")
            # dynamic_page 无原始 HTTP body；用渲染后 HTML 长度作为 response_length 的可解释替代
            response_length = rendered_html_length
        else:
            status_code, body, ct, ln, f_url = _fetch(url)
            http_status_code = str(status_code)
            content_type = ct
            response_length = str(ln)
            final_url = f_url
            if status_code >= 400:
                raise RuntimeError(f"http {status_code}; content_type={ct}; response_length={ln}; final_url={f_url}")

            # 按 source_name 做最小字段映射（MVP：只覆盖本次 3 个国内源）
            if scenario == "static_news" and name == "china_gov_policy_static":
                detail_urls = _parse_gov_policy_static_list(url, body, max_items=max_items)
                for idx, du in enumerate(detail_urls, 1):
                    _sleep_1_3s()
                    sc, detail_html, _, _, _ = _fetch(du)
                    if sc >= 400:
                        continue
                    items.append(_parse_gov_policy_detail(du, detail_html))
                    if idx >= max_items:
                        break
            elif scenario == "dynamic_page" and name == "china_gov_policy_library_dynamic":
                # 不登录、不绕反爬：先做“可达性 + 尽力抽取可见字段”的最小验证
                items = _parse_policy_library_dynamic_minimal(url, body, max_items=max_items)
            else:
                items = []

        elapsed = time.perf_counter() - start
        # nbs_data_dynamic：统计数据平台类动态页面，不以发布时间为核心字段；valid_count 不要求 publish_time
        required_fields = DEFAULT_REQUIRED_FIELDS
        if scenario == "dynamic_page" and name == "nbs_data_dynamic":
            required_fields = ["title", "content", "source", "source_url", "category", "keywords"]
        valid_count, completeness = _compute_valid_and_completeness(items, required_fields=required_fields, completeness_fields=ALL_FIELDS)

        item_count = len(items)

        # 结果判断规则（严格按需求；nbs_data_dynamic 单独规则）
        if scenario == "dynamic_page" and name == "nbs_data_dynamic":
            if item_count == 0:
                status_str = "failed"
                validation_conclusion = "验证失败，需要调整解析规则"
                error_msg = (
                    "页面可访问但动态内容未抽取到，需要继续调整选择器或等待策略；"
                    f" rendered_html_length={rendered_html_length};"
                    f" detected_links_count={detected_links_count};"
                    f" detected_text_blocks_count={detected_text_blocks_count};"
                    f" page_title={page_title};"
                    f" text_head_200={text_head_200}"
                )
            elif valid_count > 0 and completeness >= 0.6:
                status_str = "ok"
                validation_conclusion = "可落地验证通过"
                error_msg = ""
            elif item_count > 0 and completeness >= 0.6:
                status_str = "warn"
                validation_conclusion = "动态页面已抽取候选样本，但部分字段仍需优化"
                error_msg = ""
            else:
                status_str = "failed"
                validation_conclusion = "验证失败，需要调整解析规则"
                error_msg = ""
        else:
            if item_count == 0:
                validation_conclusion = "验证失败，需要调整解析规则"
                status_str = "failed"
                error_msg = ""
            else:
                if valid_count > 0 and completeness >= 0.6:
                    validation_conclusion = "可落地验证通过"
                    status_str = "ok"
                elif valid_count > 0 and completeness < 0.6:
                    validation_conclusion = "可访问但字段完整性不足"
                    status_str = "warn"
                else:
                    validation_conclusion = "验证失败，需要调整解析规则"
                    status_str = "failed"
                error_msg = ""

        return ValidationRow(
            source_name=name,
            region=region,
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed=robots_allowed,
            robots_url=robots_url,
            robots_error_type=robots_err_type,
            robots_error_message=robots_err_msg,
            status=status_str,
            item_count=item_count,
            valid_count=valid_count,
            field_completeness=round(completeness, 4),
            elapsed_seconds=round(elapsed, 6),
            error_message=error_msg,
            validation_conclusion=validation_conclusion,
            http_status_code=http_status_code,
            content_type=content_type,
            response_length=response_length,
            final_url=final_url,
            feed_title=feed_title,
            entries_count=entries_count,
            bozo=bozo,
            bozo_exception=bozo_exception,
        )
    except Exception as e:
        elapsed = time.perf_counter() - start
        msg = str(e)
        # RSS: if we already collected some diag fields, include them in error_message
        error_msg = msg
        if scenario == "rss_api" and collector == "feedparser_rss_api":
            # leave the error message as-is; it already includes key diagnostics
            pass
        return ValidationRow(
            source_name=name,
            region=region,
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed=robots_allowed,
            robots_url=robots_url,
            robots_error_type=robots_err_type,
            robots_error_message=robots_err_msg,
            status="failed",
            item_count=0,
            valid_count=0,
            field_completeness=0.0,
            elapsed_seconds=round(elapsed, 6),
            error_message=error_msg,
            validation_conclusion=f"验证失败，需要调整解析规则",
            http_status_code="",
            content_type="",
            response_length="",
            final_url="",
            feed_title="",
            entries_count="",
            bozo="",
            bozo_exception="",
        )


def _build_item_rows(source_name: str, scenario: str, collector: str, items: List[dict], required_fields: List[str]) -> List[ItemRow]:
    rows: List[ItemRow] = []
    for idx, it in enumerate(items, 1):
        if not isinstance(it, dict):
            continue
        missing = _missing_fields_for_item(it, required_fields=required_fields)
        rows.append(
            ItemRow(
                source_name=source_name,
                scenario=scenario,
                collector=collector,
                item_index=idx,
                title=str(it.get("title") or ""),
                content=str(it.get("content") or ""),
                source=str(it.get("source") or ""),
                source_url=str(it.get("source_url") or ""),
                publish_time=str(it.get("publish_time") or ""),
                category=str(it.get("category") or ""),
                keywords=(it.get("keywords") or []) if isinstance(it.get("keywords"), list) else [],
                is_valid=(len(missing) == 0),
                missing_fields=missing,
            )
        )
    return rows


def main() -> int:
    if not LOCAL_CONFIG.exists():
        print("[INFO] validation_sources.local.json not found.")
        print("[ACTION] Copy example to local and enable sources:")
        print(f"  - copy: {EXAMPLE_CONFIG} -> {LOCAL_CONFIG}")
        print("  - fill public URLs")
        print("  - set enabled=true for sources you want to validate")
        return 0

    cfg = _read_json(LOCAL_CONFIG)

    enabled_sources: List[Tuple[str, dict]] = []
    for scenario in ("static_news", "rss_api", "dynamic_page"):
        for src in cfg.get(scenario, []) or []:
            if bool(src.get("enabled")) is True:
                enabled_sources.append((scenario, src))

    if not enabled_sources:
        print("[INFO] No enabled sources. Set enabled=true in validation_sources.local.json")
        return 0

    rows: List[ValidationRow] = []
    for i, (scenario, src) in enumerate(enabled_sources, 1):
        print(f"[RUN] ({i}/{len(enabled_sources)}) scenario={scenario} name={src.get('name')} url={src.get('url')}")
        row = _validate_one(scenario, src)
        rows.append(row)

        # 源与源之间也做最小间隔（避免 burst）
        if i < len(enabled_sources):
            _sleep_1_3s()

    out_csv = STAGE2_OUT_DIR / "real_validation_result.csv"
    out_json = STAGE2_OUT_DIR / "real_validation_result.json"
    _write_csv(out_csv, rows)
    _write_json(out_json, rows)

    # items 明细输出（从已抽取结果中补齐）
    # 注意：当前实现不在 ValidationRow 中携带 items，因此这里通过“按 source 再跑一次抽取”来生成 items 明细。
    # 这是为了保持 summary 输出结构稳定、且避免大改 main/_validate_one 的返回类型。
    # 如果你希望避免重复请求，我可以再做一次小改：让 _validate_one 返回 (ValidationRow, items, required_fields)。
    item_rows = []
    for scenario, src in enabled_sources:
        name = str(src.get("name") or "")
        collector = str(src.get("collector") or "")
        url = str(src.get("url") or "")
        max_items = int(src.get("max_items") or 0) or 10

        robots_allowed, _, _, _, _ = _robots_status(url)
        if robots_allowed != "allowed":
            continue

        required_fields = DEFAULT_REQUIRED_FIELDS
        if scenario == "dynamic_page" and name == "nbs_data_dynamic":
            required_fields = ["title", "content", "source", "source_url", "category", "keywords"]

        items: List[dict] = []
        try:
            if scenario == "rss_api" and collector == "feedparser_rss_api":
                source_label = "中国日报 RSS" if name == "china_daily_china_rss" else "中国新闻网 RSS"
                items, _ = _validate_rss_feedparser(url, max_items=max_items, source_label=source_label)
            elif scenario == "dynamic_page" and name == "nbs_data_dynamic" and collector == "scrapy_playwright_dynamic":
                items, _ = _validate_nbs_data_dynamic(url, max_items=max_items)
            elif scenario == "static_news" and name == "china_gov_policy_static":
                sc, body, _, _, _ = _fetch(url)
                if sc < 400:
                    detail_urls = _parse_gov_policy_static_list(url, body, max_items=max_items)
                    for idx, du in enumerate(detail_urls, 1):
                        _sleep_1_3s()
                        s2, detail_html, _, _, _ = _fetch(du)
                        if s2 >= 400:
                            continue
                        items.append(_parse_gov_policy_detail(du, detail_html))
                        if idx >= max_items:
                            break
        except Exception:
            items = []

        item_rows.extend(_build_item_rows(name, scenario, collector, items, required_fields=required_fields))

    out_items_json = STAGE2_OUT_DIR / "real_validation_items.json"
    out_items_csv = STAGE2_OUT_DIR / "real_validation_items.csv"
    _write_items_json(out_items_json, item_rows)
    _write_items_csv(out_items_csv, item_rows)

    print(f"[OK] wrote: {out_csv}")
    print(f"[OK] wrote: {out_json}")
    print(f"[OK] wrote: {out_items_json}")
    print(f"[OK] wrote: {out_items_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

