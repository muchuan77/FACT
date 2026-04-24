from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CrawlerTaskViewSet


router = DefaultRouter()
router.register(r"crawler-tasks", CrawlerTaskViewSet, basename="crawler-tasks")

urlpatterns = [
    path("", include(router.urls)),
]

