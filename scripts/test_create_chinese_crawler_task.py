from __future__ import annotations

import argparse

import requests


def _choose_rss_source(backend: str) -> tuple[int, str, str]:
    resp = requests.get(f"{backend}/api/crawler/sources/", timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"GET /api/crawler/sources/ failed: http {resp.status_code}: {resp.text}")
    data = resp.json()
    # support both plain list and paginated format
    items = data.get("results") if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []

    candidates = []
    for s in items:
        if not isinstance(s, dict):
            continue
        if s.get("enabled") is not True:
            continue
        if s.get("source_type") != "rss":
            continue
        if s.get("adapter_name") != "rss_feedparser":
            continue
        sid = s.get("id")
        name = str(s.get("name") or "")
        url = str(s.get("base_url") or "")
        if isinstance(sid, int) and name and url:
            candidates.append((sid, name, url))

    if not candidates:
        raise RuntimeError("no available RSS sources. Please run: python manage.py seed_crawler_sources")

    # prefer 中国新闻网, else first available
    for sid, name, url in candidates:
        if "中国新闻网" in name:
            return sid, name, url
    return candidates[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-id", type=int, default=None)
    ap.add_argument("--keyword", type=str, default="社会")
    ap.add_argument("--no-keyword-filter", action="store_true", help="Disable keyword filtering (keywords=[]).")
    ap.add_argument("--max-items", type=int, default=5)
    ap.add_argument("--backend-url", type=str, default="http://127.0.0.1:8000")
    args = ap.parse_args()

    backend = args.backend_url.rstrip("/")

    if args.source_id is not None:
        source_id = int(args.source_id)
        source_name = "(user specified)"
        source_url = ""
    else:
        try:
            source_id, source_name, source_url = _choose_rss_source(backend)
        except Exception as e:
            print("[ERROR]", e)
            print("[HINT] Please run: python manage.py seed_crawler_sources")
            return 2

    print("using source_id:", source_id)
    print("using source_name:", source_name)
    print("using source_url:", source_url)

    if args.no_keyword_filter:
        task_name = "RSS中文采集测试-不过滤关键词"
        keywords = []
    else:
        task_name = f"RSS主动搜索测试-{args.keyword}"
        keywords = [args.keyword]

    payload = {
        "task_name": task_name,
        "task_type": "search",
        "keywords": keywords,
        "sources": [source_id],
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

    run = requests.post(f"{backend}/api/crawler/tasks/{task_id}/run-now/", json={}, timeout=30)
    print("run_now status_code:", run.status_code)
    print("run_now response.text:", run.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

