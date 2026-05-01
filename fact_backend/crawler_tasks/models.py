from __future__ import annotations

import hashlib
from django.db import models


class CrawlerSource(models.Model):
    """
    表示一个采集源或平台（第二阶段：RSS 真实可用；static/dynamic 预留）。
    """

    class SourceType(models.TextChoices):
        RSS = "rss", "RSS"
        STATIC = "static", "Static page"
        DYNAMIC = "dynamic", "Dynamic page"
        API = "api", "API"
        SEARCH = "search", "Search"

    name = models.CharField(max_length=200)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    base_url = models.URLField()
    adapter_name = models.CharField(max_length=100)  # rss_feedparser / scrapy_static / scrapy_playwright_dynamic
    enabled = models.BooleanField(default=True)
    robots_required = models.BooleanField(default=True)
    rate_limit_seconds = models.IntegerField(default=2)
    description = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.id}: {self.name} ({self.source_type}/{self.adapter_name})"


class TopicProfile(models.Model):
    """
    长期监控主题配置（monitor 任务优先绑定）。
    """

    name = models.CharField(max_length=200)
    keywords = models.JSONField(default=list, blank=True)  # list[str]
    exclude_keywords = models.JSONField(default=list, blank=True)  # list[str]
    category = models.CharField(max_length=100, blank=True, default="")
    risk_words = models.JSONField(default=list, blank=True)  # list[str]
    enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.id}: {self.name}"


class CrawlerTask(models.Model):
    """
    任务控制中心：monitor/search（本轮提供 run-now 同步执行 RSS）。
    """

    class TaskType(models.TextChoices):
        MONITOR = "monitor", "监控"
        SEARCH = "search", "搜索"

    class Status(models.TextChoices):
        PENDING = "pending", "待运行"
        RUNNING = "running", "运行中"
        PAUSED = "paused", "已暂停"
        STOPPED = "stopped", "已停止"
        FINISHED = "finished", "已完成"
        FAILED = "failed", "失败"

    class ScheduleType(models.TextChoices):
        ONCE = "once", "单次"
        INTERVAL = "interval", "间隔"
        CRON = "cron", "Cron"

    task_name = models.CharField(max_length=200)
    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    topic_profile = models.ForeignKey(
        TopicProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
    )
    keywords = models.JSONField(default=list, blank=True)  # list[str] for search, or override
    sources = models.ManyToManyField(CrawlerSource, related_name="tasks", blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    schedule_type = models.CharField(max_length=20, choices=ScheduleType.choices, default=ScheduleType.ONCE)
    interval_minutes = models.IntegerField(null=True, blank=True)
    max_items_per_run = models.IntegerField(default=20)
    auto_analyze = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.id}: {self.task_name} ({self.task_type}/{self.status})"


class CrawlerRun(models.Model):
    """
    某个任务的一次运行。
    """

    class Status(models.TextChoices):
        RUNNING = "running", "运行中"
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"
        CANCELED = "canceled", "取消"

    task = models.ForeignKey(CrawlerTask, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    total_fetched = models.IntegerField(default=0)
    total_valid = models.IntegerField(default=0)
    total_inserted = models.IntegerField(default=0)
    total_duplicated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"{self.id}: task={self.task_id} ({self.status})"


class CrawledItem(models.Model):
    """
    一次采集到的标准化结果（用于追踪去重、入库与关联 OpinionData）。
    """

    class Status(models.TextChoices):
        NEW = "new", "新建"
        INSERTED = "inserted", "已入库"
        DUPLICATE = "duplicate", "重复"
        FAILED = "failed", "失败"

    task = models.ForeignKey(CrawlerTask, on_delete=models.CASCADE, related_name="items")
    run = models.ForeignKey(CrawlerRun, on_delete=models.CASCADE, related_name="items")

    title = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField(blank=True, default="")
    source = models.CharField(max_length=100, blank=True, default="")
    source_url = models.URLField(blank=True, default="")
    publish_time = models.DateTimeField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True, default="")
    keywords = models.JSONField(default=list, blank=True)

    content_hash = models.CharField(max_length=64, blank=True, default="", db_index=True)
    source_url_hash = models.CharField(max_length=64, blank=True, default="", db_index=True)

    opinion_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.id}: run={self.run_id} status={self.status}"

    @staticmethod
    def sha256_hex(s: str) -> str:
        return hashlib.sha256((s or "").encode("utf-8")).hexdigest()

