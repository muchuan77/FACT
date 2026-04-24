from django.contrib import admin

from .models import CrawlerTask


@admin.register(CrawlerTask)
class CrawlerTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "task_name", "source_type", "status", "total_count", "success_count")
    search_fields = ("task_name", "source_type", "error_message")
    list_filter = ("status", "source_type")

