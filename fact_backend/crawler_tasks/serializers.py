from __future__ import annotations

from rest_framework import serializers

from .models import CrawledItem, CrawlerRun, CrawlerSource, CrawlerTask, TopicProfile


# -------------------------
# Legacy (keep /api/crawler-tasks/ working)
# -------------------------


class LegacyCrawlerTaskSerializer(serializers.ModelSerializer):
    """
    兼容 v1.0/v1.1 期间的只读接口字段形状（不破坏既有 API）。
    这些字段由新模型派生得到，并非新模型的同名字段。
    """

    source_type = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    total_count = serializers.SerializerMethodField()
    success_count = serializers.SerializerMethodField()
    error_message = serializers.SerializerMethodField()

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

    def _latest_run(self, obj: CrawlerTask) -> CrawlerRun | None:
        return obj.runs.order_by("-id").first()

    def get_source_type(self, obj: CrawlerTask) -> str:
        src = obj.sources.first()
        return (src.source_type if src else "")

    def get_start_time(self, obj: CrawlerTask):
        r = self._latest_run(obj)
        return getattr(r, "started_at", None) if r else None

    def get_end_time(self, obj: CrawlerTask):
        r = self._latest_run(obj)
        return getattr(r, "finished_at", None) if r else None

    def get_total_count(self, obj: CrawlerTask) -> int:
        r = self._latest_run(obj)
        return int(getattr(r, "total_fetched", 0) if r else 0)

    def get_success_count(self, obj: CrawlerTask) -> int:
        r = self._latest_run(obj)
        return int(getattr(r, "total_valid", 0) if r else 0)

    def get_error_message(self, obj: CrawlerTask) -> str:
        r = self._latest_run(obj)
        return str(getattr(r, "error_message", "") if r else "")


# -------------------------
# v1.3.0 crawler control center APIs
# -------------------------


class CrawlerSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlerSource
        fields = [
            "id",
            "name",
            "source_type",
            "base_url",
            "adapter_name",
            "enabled",
            "robots_required",
            "rate_limit_seconds",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TopicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicProfile
        fields = [
            "id",
            "name",
            "keywords",
            "exclude_keywords",
            "category",
            "risk_words",
            "enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CrawlerTaskSerializer(serializers.ModelSerializer):
    sources = serializers.PrimaryKeyRelatedField(many=True, queryset=CrawlerSource.objects.all(), required=False)

    class Meta:
        model = CrawlerTask
        fields = [
            "id",
            "task_name",
            "task_type",
            "topic_profile",
            "keywords",
            "sources",
            "status",
            "schedule_type",
            "interval_minutes",
            "max_items_per_run",
            "auto_analyze",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        sources = validated_data.pop("sources", [])
        obj = super().create(validated_data)
        if sources:
            obj.sources.set(sources)
        return obj


class CrawlerRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlerRun
        fields = [
            "id",
            "task",
            "status",
            "started_at",
            "finished_at",
            "total_fetched",
            "total_valid",
            "total_inserted",
            "total_duplicated",
            "error_message",
        ]
        read_only_fields = fields


class CrawledItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawledItem
        fields = [
            "id",
            "task",
            "run",
            "title",
            "content",
            "source",
            "source_url",
            "publish_time",
            "category",
            "keywords",
            "content_hash",
            "source_url_hash",
            "opinion_id",
            "status",
            "created_at",
        ]
        read_only_fields = fields

