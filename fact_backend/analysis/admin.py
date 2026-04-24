from django.contrib import admin

from .models import AnalysisResult


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("id", "opinion", "rumor_label", "sentiment_label", "model_name", "analyzed_at")
    search_fields = ("opinion__title", "model_name", "rumor_label", "sentiment_label")
    list_filter = ("rumor_label", "sentiment_label", "model_name")

