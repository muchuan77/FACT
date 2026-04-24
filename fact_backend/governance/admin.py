from django.contrib import admin

from .models import GovernanceRecord


@admin.register(GovernanceRecord)
class GovernanceRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "warning", "action_type", "operator", "created_at")
    search_fields = ("action_type", "action_content", "operator")
    list_filter = ("action_type",)

