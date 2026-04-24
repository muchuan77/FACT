from django.db import models


class GovernanceRecord(models.Model):
    """
    治理响应记录（MVP）。
    """

    warning = models.ForeignKey(
        "risk_warnings.RiskWarning",
        on_delete=models.CASCADE,
        related_name="governance_records",
    )

    action_type = models.CharField(max_length=50)
    action_content = models.TextField()
    effect_description = models.TextField(blank=True, default="")
    operator = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.id}: {self.action_type} warning={self.warning_id}"

