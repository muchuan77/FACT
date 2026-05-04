from __future__ import annotations

from django.core.management.base import BaseCommand

from crawler_tasks.models import CrawlerSource


# 顺序与 source_code 固定；幂等键为 source_code（不再用 name / id / base_url 作为识别主键）
DEFAULT_SOURCES: list[dict] = [
    {
        "source_code": "chinanews_society_rss",
        "name": "中国新闻网社会新闻 RSS",
        "source_type": CrawlerSource.SourceType.RSS,
        "base_url": "https://www.chinanews.com.cn/rss/society.xml",
        "adapter_name": "rss_feedparser",
        "enabled": True,
        "robots_required": True,
        "rate_limit_seconds": 2,
        "description": "v1.3.0 默认 RSS 源（备用/推荐）",
    },
    {
        "source_code": "china_daily_rss",
        "name": "中国日报 China RSS",
        "source_type": CrawlerSource.SourceType.RSS,
        "base_url": "http://www.chinadaily.com.cn/rss/china_rss.xml",
        "adapter_name": "rss_feedparser",
        "enabled": True,
        "robots_required": True,
        "rate_limit_seconds": 2,
        "description": "v1.3.0 默认 RSS 源（备用/推荐）",
    },
    {
        "source_code": "gov_zhengce_static",
        "name": "中国政府网政策（静态列表+详情）",
        "source_type": CrawlerSource.SourceType.STATIC,
        "base_url": "https://www.gov.cn/zhengce/",
        "adapter_name": "scrapy_static",
        "enabled": True,
        "robots_required": True,
        "rate_limit_seconds": 2,
        "description": "v1.4.0 Scrapy 静态适配器；公开源入口。本地联调见 fact_crawler/static_demo/README.txt",
    },
    {
        "source_code": "local_static_demo",
        "name": "本地静态演示列表（需 http.server，默认关闭）",
        "source_type": CrawlerSource.SourceType.STATIC,
        "base_url": "http://127.0.0.1:8765/list.html",
        "adapter_name": "scrapy_static",
        "enabled": True,
        "robots_required": False,
        "rate_limit_seconds": 0,
        "description": "在仓库 fact_crawler/static_demo 目录执行: python -m http.server 8765 ，启用本源并设 base_url 同上；本地演示不做 robots 检查",
    },
    {
        "source_code": "local_dynamic_demo",
        "name": "本地动态演示页面（需 http.server，默认关闭）",
        "source_type": CrawlerSource.SourceType.DYNAMIC,
        "base_url": "http://127.0.0.1:8766/index.html",
        "adapter_name": "scrapy_playwright_dynamic",
        "enabled": False,
        "robots_required": False,
        "rate_limit_seconds": 0,
        "description": "v1.5.0 Scrapy+Playwright；见 fact_crawler/dynamic_demo/README.txt；需 playwright install chromium",
    },
]


class Command(BaseCommand):
    help = "Seed default crawler sources (v1.5.0: upsert by source_code, includes local_dynamic_demo)"

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for spec in DEFAULT_SOURCES:
            code = spec["source_code"]
            defaults = {k: v for k, v in spec.items() if k != "source_code"}
            obj, was_created = CrawlerSource.objects.update_or_create(
                source_code=code,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] seed_crawler_sources done. created={created} updated={updated} "
                f"(upsert key=source_code, total_specs={len(DEFAULT_SOURCES)})"
            )
        )
