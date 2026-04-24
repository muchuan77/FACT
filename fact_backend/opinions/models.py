from django.db import models


class OpinionData(models.Model):
    """
    原始舆情数据（MVP）。
    """

    class Status(models.TextChoices):
        NEW = "new", "新建"
        ANALYZED = "analyzed", "已分析"
        WARNED = "warned", "已预警"
        CLOSED = "closed", "已关闭"

    title = models.CharField(max_length=255)
    content = models.TextField()
    source = models.CharField(max_length=100, blank=True, default="")
    source_url = models.URLField(blank=True, default="")
    publish_time = models.DateTimeField(null=True, blank=True)
    crawl_time = models.DateTimeField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True, default="")
    raw_label = models.CharField(max_length=100, blank=True, default="")
    keywords = models.JSONField(default=list, blank=True, verbose_name="关键词")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.id}: {self.title}"

