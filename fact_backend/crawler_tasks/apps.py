from django.apps import AppConfig


class CrawlerTasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crawler_tasks"
    verbose_name = "爬虫任务"

