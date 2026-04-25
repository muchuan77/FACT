from __future__ import annotations

import csv
import json
import random
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


REQUIRED_FIELDS = ["title", "content", "source", "source_url", "publish_time", "category", "keywords"]


@dataclass
class ValidationRow:
    source_name: str
    scenario: str
    url: str
    collector: str
    robots_allowed: bool
    status: str
    item_count: int
    valid_count: int
    field_completeness: float
    elapsed_seconds: float
    error_message: str
    validation_conclusion: str


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


def _fetch(url: str, timeout: float = 15.0) -> Tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FACT-crawler-selection-experiment/1.0 (public validation; respect robots.txt)",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read()
        return int(getattr(resp, "status", 200)), raw.decode(charset, errors="replace")


def _robots_allowed(url: str, user_agent: str = "*") -> Tuple[bool, str]:
    """
    返回 (allowed, reason)。无法确认时返回 (False, reason) 并让上层记录 skipped。
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return False, "invalid url"
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(user_agent, url)
        return bool(allowed), f"robots={robots_url}"
    except Exception as e:
        return False, f"robots check failed: {e}"


def _compute_field_completeness(items: List[dict]) -> Tuple[int, float]:
    if not items:
        return 0, 0.0
    total = 0
    ok = 0
    valid = 0
    for it in items:
        item_ok = True
        for f in REQUIRED_FIELDS:
            total += 1
            v = it.get(f)
            if f == "keywords":
                good = isinstance(v, list)
            else:
                good = v is not None and v != ""
            ok += 1 if good else 0
            if not good:
                item_ok = False
        if item_ok:
            valid += 1
    return valid, (ok / total if total else 0.0)


def _parse_static_minimal(url: str, html: str) -> List[dict]:
    # 真实验证框架：不追求通用解析，仅做“能否拿到核心字段”的可落地验证
    def between(s: str, a: str, b: str) -> str:
        i = s.find(a)
        if i < 0:
            return ""
        j = s.find(b, i + len(a))
        if j < 0:
            return ""
        return s[i + len(a) : j].strip()

    title = between(html, "<title>", "</title>") or between(html, "<h1>", "</h1>")
    content = between(html, "<article", "</article>") or between(html, "<body", "</body>")
    # 真实网站很难按固定规则提取，这里只验证“可获取页面文本”
    content = content[:5000]
    return [
        {
            "title": title,
            "content": content,
            "source": urllib.parse.urlparse(url).netloc,
            "source_url": url,
            "publish_time": "",
            "category": "",
            "keywords": [],
        }
    ]


def _parse_rss_minimal(url: str, xml_text: str) -> List[dict]:
    # RSS 解析：只取 item/title/link/description/category/pubDate 等常见字段
    import xml.etree.ElementTree as ET

    items: List[dict] = []
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return items
    for it in channel.findall("item")[:20]:
        items.append(
            {
                "title": (it.findtext("title") or "").strip(),
                "content": (it.findtext("description") or "").strip(),
                "source": urllib.parse.urlparse(url).netloc,
                "source_url": (it.findtext("link") or "").strip() or url,
                "publish_time": (it.findtext("pubDate") or "").strip(),
                "category": (it.findtext("category") or "").strip(),
                "keywords": [],
            }
        )
    return items


def _validate_one(scenario: str, src: dict) -> ValidationRow:
    name = str(src.get("name") or "")
    url = str(src.get("url") or "")
    collector = str(src.get("collector") or "")

    # 合规提示（记录到结论中，避免静默抓取）
    compliance_note = "no-login/no-captcha/no-bypass/no-PII + respect robots + rate-limit"

    if not url or not collector:
        return ValidationRow(
            source_name=name or "(missing)",
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed=False,
            status="skipped",
            item_count=0,
            valid_count=0,
            field_completeness=0.0,
            elapsed_seconds=0.0,
            error_message="missing url or collector",
            validation_conclusion=f"skipped: invalid config ({compliance_note})",
        )

    allowed, robots_reason = _robots_allowed(url)
    if not allowed:
        return ValidationRow(
            source_name=name,
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed=False,
            status="skipped",
            item_count=0,
            valid_count=0,
            field_completeness=0.0,
            elapsed_seconds=0.0,
            error_message=robots_reason,
            validation_conclusion=f"skipped: robots not allowed/unknown ({compliance_note})",
        )

    start = time.perf_counter()
    try:
        status_code, body = _fetch(url)
        if status_code >= 400:
            raise RuntimeError(f"http {status_code}")

        # 根据场景选择最小解析方式（框架验证，不追求生产级）
        if scenario == "static_news":
            items = _parse_static_minimal(url, body)
        elif scenario == "rss_api":
            items = _parse_rss_minimal(url, body)
        elif scenario == "dynamic_page":
            # 框架：动态页面通常需要 Playwright。这里不自动执行浏览器，仅标记可达性。
            items = []
        else:
            items = []

        elapsed = time.perf_counter() - start
        valid_count, completeness = _compute_field_completeness(items)

        if scenario == "dynamic_page" and collector == "playwright_dynamic":
            conclusion = "reachable; playwright required (framework only)"
            status_str = "ok"
        else:
            conclusion = "ok" if items else "reachable but parsed empty"
            status_str = "ok" if items else "warn"

        return ValidationRow(
            source_name=name,
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed=True,
            status=status_str,
            item_count=len(items),
            valid_count=valid_count,
            field_completeness=round(completeness, 4),
            elapsed_seconds=round(elapsed, 6),
            error_message="",
            validation_conclusion=f"{conclusion} ({compliance_note})",
        )
    except Exception as e:
        elapsed = time.perf_counter() - start
        return ValidationRow(
            source_name=name,
            scenario=scenario,
            url=url,
            collector=collector,
            robots_allowed=True,
            status="failed",
            item_count=0,
            valid_count=0,
            field_completeness=0.0,
            elapsed_seconds=round(elapsed, 6),
            error_message=str(e),
            validation_conclusion=f"failed: {e} ({compliance_note})",
        )


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
        # rate limit: sleep 1~3s between requests
        if i < len(enabled_sources):
            time.sleep(random.uniform(1.0, 3.0))

    out_csv = BASE_DIR / "results" / "real_validation_result.csv"
    out_json = BASE_DIR / "results" / "real_validation_result.json"
    _write_csv(out_csv, rows)
    _write_json(out_json, rows)

    print(f"[OK] wrote: {out_csv}")
    print(f"[OK] wrote: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

