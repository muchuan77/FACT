from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

# 用于乱码检测（与 fact_crawler 一致）
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from fact_crawler.crawler.normalizer import looks_like_mojibake  # noqa: E402


def _sources_list(backend: str) -> list[dict]:
    resp = requests.get(f"{backend}/api/crawler/sources/", timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"GET /api/crawler/sources/ failed: http {resp.status_code}: {resp.text}")
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        items = data.get("results")
        if isinstance(items, list):
            return items
    return []


def _pick_by_code(sources: list[dict], code: str) -> dict | None:
    c = (code or "").strip()
    if not c:
        return None
    for s in sources:
        if not isinstance(s, dict):
            continue
        if str(s.get("source_code") or "") == c:
            return s
    return None


def _pick_by_id(sources: list[dict], sid: int) -> dict | None:
    for s in sources:
        if not isinstance(s, dict):
            continue
        if s.get("id") == sid:
            return s
    return None


def _resolve_source(
    backend: str,
    mode: str,
    source_id: int | None,
    source_code: str | None,
) -> tuple[dict, list[str]]:
    """
    返回 (source_dict, warnings)。
    """
    warnings: list[str] = []
    sources = _sources_list(backend)
    if not sources:
        raise RuntimeError("sources 列表为空。请先执行: python manage.py seed_crawler_sources")

    if source_code and source_id is not None:
        warnings.append("同时指定了 --source-code 与 --source-id，已按 source_code 解析，忽略 source_id。")

    if source_code:
        src = _pick_by_code(sources, source_code)
        if not src:
            codes = sorted(
                {str(s.get("source_code") or "") for s in sources if isinstance(s, dict) and s.get("source_code")}
            )
            raise RuntimeError(f"未找到 source_code={source_code!r}。当前可用: {codes}")
        return src, warnings

    if source_id is not None:
        warnings.append("使用 --source-id 仅适合临时调试；清库后主键会变，推荐 --source-code。")
        src = _pick_by_id(sources, int(source_id))
        if not src:
            raise RuntimeError(f"未找到 id={source_id} 的 CrawlerSource。")
        return src, warnings

    # 自动：按 mode 选默认 source_code
    if mode == "static":
        code = "local_static_demo"
    else:
        code = "chinanews_society_rss"
    src = _pick_by_code(sources, code)
    if src:
        return src, warnings

    # 回退：按类型挑第一个可用源
    want_type = "static" if mode == "static" else "rss"
    want_adapter = "scrapy_static" if mode == "static" else "rss_feedparser"
    for s in sources:
        if not isinstance(s, dict):
            continue
        if s.get("enabled") is not True:
            continue
        if s.get("source_type") != want_type or s.get("adapter_name") != want_adapter:
            continue
        return s, warnings

    raise RuntimeError(
        f"无法为 mode={mode} 自动选择源（缺 {code}）。请显式传入 --source-code 或先 seed。"
    )


def _validate_mode_source(mode: str, src: dict) -> str | None:
    if mode == "static":
        if src.get("source_type") != "static" or src.get("adapter_name") != "scrapy_static":
            return (
                f"--mode static 要求 source_type=static 且 adapter_name=scrapy_static；"
                f"当前为 source_type={src.get('source_type')!r} adapter_name={src.get('adapter_name')!r}"
            )
    else:
        if src.get("source_type") != "rss" or src.get("adapter_name") != "rss_feedparser":
            return (
                f"--mode rss 要求 source_type=rss 且 adapter_name=rss_feedparser；"
                f"当前为 source_type={src.get('source_type')!r} adapter_name={src.get('adapter_name')!r}"
            )
    return None


def _print_sample_items(backend: str, task_id: int, run_id: int) -> None:
    items_url = f"{backend}/api/crawler/runs/{run_id}/items/"
    ir = requests.get(items_url, timeout=15)
    print("sample_items GET", items_url, "status", ir.status_code)
    if ir.status_code >= 400:
        print(ir.text)
        return
    data = ir.json()
    rows = data.get("results") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        rows = []
    for row in rows[:2]:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "")
        content = str(row.get("content") or "")
        source = str(row.get("source") or "")
        source_url = str(row.get("source_url") or "")
        print("--- item ---")
        print("  title:", title[:200])
        print("  content[0:100]:", content[:100])
        print("  source:", source[:200])
        print("  source_url:", source_url)
        blob = title + content + source
        if looks_like_mojibake(blob):
            print("  [WARN] mojibake detected in title/content/source")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("rss", "static"), default="rss", help="Pick default source_code when not specified.")
    ap.add_argument("--source-id", type=int, default=None)
    ap.add_argument("--source-code", type=str, default=None, help="Stable slug (recommended), e.g. local_static_demo.")
    ap.add_argument("--keyword", type=str, default="社会")
    ap.add_argument("--no-keyword-filter", action="store_true", help="Disable keyword filtering (keywords=[]).")
    ap.add_argument("--max-items", type=int, default=5)
    ap.add_argument("--backend-url", type=str, default="http://127.0.0.1:8000")
    args = ap.parse_args()

    backend = args.backend_url.rstrip("/")

    try:
        src, warns = _resolve_source(
            backend,
            args.mode,
            args.source_id,
            (args.source_code or "").strip() or None,
        )
    except Exception as e:
        print("[ERROR]", e)
        print("[HINT] Please run: python manage.py migrate && python manage.py seed_crawler_sources")
        return 2

    for w in warns:
        print("[WARN]", w, flush=True)

    err = _validate_mode_source(args.mode, src)
    if err:
        print("[ERROR]", err, flush=True)
        return 2

    sid = src.get("id")
    if not isinstance(sid, int):
        print("[ERROR] resolved source has no integer id:", src, flush=True)
        return 2

    print("resolved source:")
    print("  source_id:", sid)
    print("  source_code:", src.get("source_code"))
    print("  source_name:", src.get("name"))
    print("  source_type:", src.get("source_type"))
    print("  adapter_name:", src.get("adapter_name"))
    print("  base_url:", src.get("base_url"))

    print("using mode:", args.mode)

    if args.no_keyword_filter:
        task_name = "中文采集测试-不过滤关键词" if args.mode == "rss" else "静态采集测试-不过滤关键词"
        keywords = []
    else:
        task_name = f"{'RSS' if args.mode == 'rss' else '静态'}主动搜索测试-{args.keyword}"
        keywords = [args.keyword]

    payload = {
        "task_name": task_name,
        "task_type": "search",
        "keywords": keywords,
        "sources": [sid],
        "schedule_type": "once",
        "interval_minutes": 60,
        "max_items_per_run": args.max_items,
        "auto_analyze": True,
    }

    resp = requests.post(f"{backend}/api/crawler/tasks/", json=payload, timeout=10)
    print("create_task status_code:", resp.status_code)
    print("create_task response.text:", resp.text)
    if resp.status_code >= 400:
        return 1

    data = resp.json()
    task_id = data.get("id")
    print("task_id:", task_id)
    if not task_id:
        return 2

    run = requests.post(f"{backend}/api/crawler/tasks/{task_id}/run-now/", json={}, timeout=120)
    print("run_now status_code:", run.status_code)
    print("run_now response.text:", run.text)
    if run.status_code >= 400:
        return 1
    run_payload = run.json()
    fetched = int(run_payload.get("total_fetched") or 0)
    inserted = int(run_payload.get("total_inserted") or 0)
    run_id = run_payload.get("run_id")
    if args.mode == "static" and fetched == 0:
        print(
            "[HINT] static run total_fetched=0：请查看运行 Django 的终端中 "
            "[gov.cn zhengce list diagnostics]（detail_links_count、list_page_response.status、"
            "href_preview_first20、Content-Type、reason）及 [scrapy_static][gov.cn subprocess stderr]",
            flush=True,
        )
    if inserted > 0 and run_id is not None:
        rr = requests.get(f"{backend}/api/crawler/tasks/{task_id}/runs/", timeout=15)
        print("runs GET status:", rr.status_code)
        if rr.ok:
            rdata = rr.json()
            rlist = rdata.get("results") if isinstance(rdata, dict) else rdata
            if isinstance(rlist, list) and rlist:
                print("latest run id:", rlist[0].get("id") if isinstance(rlist[0], dict) else None)
        _print_sample_items(backend, int(task_id), int(run_id))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
