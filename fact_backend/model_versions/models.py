from django.db import models


class ModelVersion(models.Model):
    """
    模型版本记录（MVP：用于登记模型版本与指标）。
    """

    model_name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, blank=True, default="")
    version = models.CharField(max_length=50)
    metrics = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.model_name}:{self.version}"

