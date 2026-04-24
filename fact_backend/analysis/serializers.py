from rest_framework import serializers

from .models import AnalysisResult


class AnalysisResultSerializer(serializers.ModelSerializer):
    opinion_title = serializers.CharField(source="opinion.title", read_only=True)

    class Meta:
        model = AnalysisResult
        fields = [
            "id",
            "opinion",
            "opinion_title",
            "rumor_label",
            "rumor_probability",
            "sentiment_label",
            "sentiment_probability",
            "keywords",
            "model_name",
            "analyzed_at",
        ]
        read_only_fields = fields

