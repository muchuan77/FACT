from django.contrib import admin

from .models import ModelVersion


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "model_name", "model_type", "version", "is_active", "created_at")
    search_fields = ("model_name", "model_type", "version")
    list_filter = ("is_active", "model_type")

