# v1.4.1: stable business key for CrawlerSource

from django.db import migrations, models


def backfill_source_code(apps, schema_editor):
    CrawlerSource = apps.get_model("crawler_tasks", "CrawlerSource")
    needles = (
        ("www.gov.cn/zhengce", "gov_zhengce_static"),
        ("127.0.0.1:8765", "local_static_demo"),
        ("localhost:8765", "local_static_demo"),
        ("chinanews.com.cn/rss/society", "chinanews_society_rss"),
        ("chinadaily.com.cn/rss/china_rss", "china_daily_rss"),
    )
    for obj in CrawlerSource.objects.all().order_by("id"):
        if (getattr(obj, "source_code", None) or "").strip():
            continue
        url = (getattr(obj, "base_url", "") or "").lower()
        code = None
        for needle, c in needles:
            if needle in url:
                code = c
                break
        if not code:
            code = f"legacy_{obj.pk}"
        base = code
        n = 0
        while (
            CrawlerSource.objects.filter(source_code=code)
            .exclude(pk=obj.pk)
            .exists()
        ):
            n += 1
            code = f"{base}_{n}"
        obj.source_code = code
        obj.save(update_fields=["source_code"])


def reverse_backfill(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("crawler_tasks", "0002_v1_3_crawler_control_center"),
    ]

    operations = [
        migrations.AddField(
            model_name="crawlersource",
            name="source_code",
            field=models.SlugField(blank=True, max_length=100, null=True),
        ),
        migrations.RunPython(backfill_source_code, reverse_backfill),
        migrations.AlterField(
            model_name="crawlersource",
            name="source_code",
            field=models.SlugField(max_length=100, unique=True),
        ),
    ]
