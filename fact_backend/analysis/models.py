from django.db import models


class AnalysisResult(models.Model):
    """
    模型分析结果（MVP：用于落库展示，不承载推理逻辑）。
    """

    opinion = models.ForeignKey(
        "opinions.OpinionData",
        on_delete=models.CASCADE,
        related_name="analysis_results",
    )

    rumor_label = models.CharField(max_length=50, blank=True, default="")
    rumor_probability = models.FloatField(default=0.0)
    sentiment_label = models.CharField(max_length=50, blank=True, default="")
    sentiment_probability = models.FloatField(default=0.0)

    keywords = models.JSONField(default=list, blank=True)
    model_name = models.CharField(max_length=100, blank=True, default="")
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.id}: opinion={self.opinion_id} model={self.model_name}"

