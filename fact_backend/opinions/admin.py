from django.contrib import admin

from .models import OpinionData


@admin.register(OpinionData)
class OpinionDataAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "source", "status", "created_at")
    search_fields = ("title", "content", "source")
    list_filter = ("status", "source", "category")

