from rest_framework import serializers

from .models import RiskWarning


class RiskWarningSerializer(serializers.ModelSerializer):
    opinion_title = serializers.CharField(source="opinion.title", read_only=True)

    class Meta:
        model = RiskWarning
        fields = [
            "id",
            "opinion",
            "opinion_title",
            "analysis_result",
            "risk_score",
            "risk_level",
            "warning_reason",
            "status",
            "created_at",
        ]
        read_only_fields = fields

