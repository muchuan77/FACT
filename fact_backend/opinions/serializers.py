from rest_framework import serializers

from .models import OpinionData


class OpinionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionData
        fields = [
            "id",
            "title",
            "content",
            "source",
            "source_url",
            "publish_time",
            "crawl_time",
            "category",
            "raw_label",
            "keywords",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

