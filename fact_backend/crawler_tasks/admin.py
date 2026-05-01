from django.contrib import admin

from .models import CrawledItem, CrawlerRun, CrawlerSource, CrawlerTask, TopicProfile


@admin.register(CrawlerSource)
class CrawlerSourceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "source_type", "adapter_name", "enabled", "rate_limit_seconds", "robots_required")
    search_fields = ("name", "base_url", "adapter_name")
    list_filter = ("source_type", "adapter_name", "enabled", "robots_required")


@admin.register(TopicProfile)
class TopicProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "enabled")
    search_fields = ("name", "category")
    list_filter = ("enabled", "category")


@admin.register(CrawlerTask)
class CrawlerTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "task_name", "task_type", "status", "schedule_type", "max_items_per_run", "auto_analyze")
    search_fields = ("task_name",)
    list_filter = ("task_type", "status", "schedule_type", "auto_analyze")


@admin.register(CrawlerRun)
class CrawlerRunAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "status", "started_at", "finished_at", "total_fetched", "total_valid", "total_inserted", "total_duplicated")
    search_fields = ("task__task_name", "error_message")
    list_filter = ("status",)


@admin.register(CrawledItem)
class CrawledItemAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "run", "status", "source", "source_url", "opinion_id", "created_at")
    search_fields = ("title", "source", "source_url", "content_hash", "source_url_hash")
    list_filter = ("status", "source", "category")
