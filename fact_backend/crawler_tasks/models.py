from django.db import models


class CrawlerTask(models.Model):
    """
    爬虫任务记录（MVP：不接入真实爬虫，仅用于记录任务状态）。
    """

    class Status(models.TextChoices):
        PENDING = "pending", "待运行"
        RUNNING = "running", "运行中"
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"

    task_name = models.CharField(max_length=200)
    source_type = models.CharField(max_length=50, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    total_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"{self.id}: {self.task_name} ({self.status})"

