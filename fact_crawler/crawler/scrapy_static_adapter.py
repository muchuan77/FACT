from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from scrapy.utils.log import configure_logging

from .base_adapter import AdapterContext, BaseAdapter
from .keyword_extractor import extract_keywords
from .models import OpinionItem
from .normalizer import (
    keyword_exclude,
    keyword_match,
    looks_like_mojibake,
    parse_chinese_date_loose,
    parse_datetime_loose,
)


def _repo_root() -> Path:
    # fact_crawler/crawler/scrapy_static_adapter.py -> parents[2] == FACT
    return Path(__file__).resolve().parents[2]


class ScrapyStaticAdapter(BaseAdapter):
    adapter_name = "scrapy_static"

    def fetch(self, ctx: AdapterContext) -> list[OpinionItem]:
        print(
            f"[scrapy_static] source={ctx.source_name} url={ctx.base_url} max_items={ctx.max_items} "
            f"delay={ctx.rate_limit_seconds} robots={ctx.robots_required}"
        )

        cfg: dict[str, Any] = {
            "base_url": ctx.base_url,
            "source_name": ctx.source_name,
            "max_items": ctx.max_items,
            "rate_limit_seconds": float(ctx.rate_limit_seconds or 0),
            "robots_required": bool(ctx.robots_required),
        }

        if os.environ.get("FACT_SCRAPY_STATIC_INPROCESS") == "1":
            collector = self._collect_in_process(cfg)
        else:
            collector = self._collect_subprocess(cfg)

        out: list[OpinionItem] = []
        for raw in collector:
            title = (raw.get("title") or "").strip()
            content = (raw.get("content") or "").strip()
            source_url = (raw.get("source_url") or "").strip()
            if not title or not source_url:
                continue
            article_src = (raw.get("article_source") or "").strip()
            source_display = article_src or ctx.source_name
            if looks_like_mojibake(title) or looks_like_mojibake(content) or looks_like_mojibake(source_display):
                print(
                    f"[scrapy_static][SKIP mojibake] url={source_url!r} "
                    f"title_sample={title[:60]!r} source_sample={source_display[:60]!r}"
                )
                continue
            if keyword_exclude(title, content, ctx.exclude_keywords):
                continue
            if not keyword_match(title, content, ctx.keywords):
                continue

            pub_s = raw.get("publish_time_str") or ""
            pt = parse_datetime_loose(str(pub_s)) or parse_chinese_date_loose(str(pub_s))

            page_cat = (raw.get("page_category") or "").strip()
            cat = (ctx.category or page_cat or "static_news")[:200]

            kws = extract_keywords(title, content, risk_words=ctx.risk_words, limit=8)
            html_kw = raw.get("html_keywords") or []
            if isinstance(html_kw, list):
                for k in html_kw:
                    if isinstance(k, str) and k.strip() and k.strip() not in kws and len(kws) < 8:
                        kws.append(k.strip())
            out.append(
                OpinionItem(
                    title=title,
                    content=content,
                    source=source_display[:100],
                    source_url=source_url,
                    publish_time=pt,
                    category=cat,
                    raw_label="scrapy_static",
                    keywords=kws,
                )
            )
            if len(out) >= ctx.max_items:
                break

        print(f"[scrapy_static] source={ctx.source_name} raw={len(collector)} matched={len(out)}")
        return out

    def _collect_subprocess(self, cfg: dict[str, Any]) -> list[dict[str, Any]]:
        repo = _repo_root()
        env = os.environ.copy()
        root = str(repo)
        env["PYTHONPATH"] = root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        timeout_s = int(os.environ.get("FACT_SCRAPY_SUBPROCESS_TIMEOUT", "300"))
        stdin_bytes = json.dumps(cfg, ensure_ascii=True).encode("ascii")
        proc = subprocess.run(
            [sys.executable, "-m", "fact_crawler.crawler.scrapy_static.subprocess_runner"],
            input=stdin_bytes,
            capture_output=True,
            timeout=timeout_s,
            env=env,
            cwd=root,
        )
        err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        out_b = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        base = (cfg.get("base_url") or "").lower()
        if "gov.cn" in base and "zhengce" in base and err:
            print(
                "[scrapy_static][gov.cn subprocess stderr — diagnostics]\n" + err,
                file=sys.stderr,
                flush=True,
            )
        if proc.returncode != 0:
            raise RuntimeError(err or out_b or f"scrapy subprocess exit={proc.returncode}")
        if not out_b:
            return []
        collector: list[dict[str, Any]] = json.loads(out_b)
        base_u = (cfg.get("base_url") or "").lower()
        if "gov.cn" in base_u and "zhengce" in base_u:
            for raw in collector:
                if isinstance(raw, dict) and not (raw.get("title") or "").strip():
                    print(
                        "[scrapy_static][gov.cn] collector item missing title; see stderr above for "
                        "[gov.cn zhengce detail skip] or [gov.cn zhengce detail title_empty_debug]",
                        file=sys.stderr,
                        flush=True,
                    )
                    break
        for i, raw in enumerate(collector[:2]):
            if not isinstance(raw, dict):
                continue
            print(
                f"[scrapy_static][RAW sample {i}] title={raw.get('title')!r} "
                f"source={raw.get('article_source')!r}",
                file=sys.stderr,
                flush=True,
            )
        return collector

    def _collect_in_process(self, cfg: dict[str, Any]) -> list[dict[str, Any]]:
        configure_logging(install_root_handler=False)
        from .scrapy_static.run_spider import run_collect_raw

        return run_collect_raw(cfg)
