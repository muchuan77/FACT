from django.db import models


class RiskWarning(models.Model):
    """
    风险预警结果（MVP）。
    """

    class RiskLevel(models.TextChoices):
        LOW = "low", "低"
        MEDIUM = "medium", "中"
        HIGH = "high", "高"

    class Status(models.TextChoices):
        OPEN = "open", "未处理"
        PROCESSING = "processing", "处理中"
        CLOSED = "closed", "已关闭"

    opinion = models.ForeignKey(
        "opinions.OpinionData",
        on_delete=models.CASCADE,
        related_name="risk_warnings",
    )
    analysis_result = models.ForeignKey(
        "analysis.AnalysisResult",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_warnings",
    )

    risk_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.LOW)
    warning_reason = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.id}: {self.risk_level} opinion={self.opinion_id}"

