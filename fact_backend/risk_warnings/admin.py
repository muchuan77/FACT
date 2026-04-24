from django.contrib import admin

from .models import RiskWarning


@admin.register(RiskWarning)
class RiskWarningAdmin(admin.ModelAdmin):
    list_display = ("id", "opinion", "risk_level", "risk_score", "status", "created_at")
    search_fields = ("opinion__title", "warning_reason")
    list_filter = ("risk_level", "status")

