from rest_framework import serializers

from .models import CrawlerTask


class CrawlerTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlerTask
        fields = [
            "id",
            "task_name",
            "source_type",
            "status",
            "start_time",
            "end_time",
            "total_count",
            "success_count",
            "error_message",
        ]
        read_only_fields = fields

