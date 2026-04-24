from rest_framework import serializers

from .models import ModelVersion


class ModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelVersion
        fields = [
            "id",
            "model_name",
            "model_type",
            "version",
            "metrics",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields

