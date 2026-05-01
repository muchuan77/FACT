from __future__ import annotations

from django.core.management.base import BaseCommand

from crawler_tasks.models import CrawlerSource


class Command(BaseCommand):
    help = "Seed default crawler sources (v1.3.0)"

    def handle(self, *args, **options):
        defaults = [
            {
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
                "name": "中国日报 China RSS",
                "source_type": CrawlerSource.SourceType.RSS,
                "base_url": "http://www.chinadaily.com.cn/rss/china_rss.xml",
                "adapter_name": "rss_feedparser",
                "enabled": True,
                "robots_required": True,
                "rate_limit_seconds": 2,
                "description": "v1.3.0 默认 RSS 源（备用/推荐）",
            },
        ]

        created = 0
        updated = 0
        skipped = 0
        for d in defaults:
            base_url = d["base_url"]
            obj = CrawlerSource.objects.filter(base_url=base_url).first()
            if obj is None:
                CrawlerSource.objects.create(**d)
                created += 1
                continue

            # 已存在则强制修复：以 base_url 为唯一识别依据；name 若乱码/不匹配则更新为正确中文
            changed = False
            for k, v in d.items():
                if getattr(obj, k) != v:
                    setattr(obj, k, v)
                    changed = True
            if changed:
                obj.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"[OK] seed_crawler_sources done. created={created} updated={updated} skipped={skipped}")
        )

