from rest_framework import serializers

from .models import GovernanceRecord


class GovernanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernanceRecord
        fields = [
            "id",
            "warning",
            "action_type",
            "action_content",
            "effect_description",
            "operator",
            "created_at",
        ]
        read_only_fields = fields

