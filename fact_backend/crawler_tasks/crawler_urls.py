from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CrawledItemViewSet,
    CrawlerRunViewSet,
    CrawlerSourceViewSet,
    CrawlerTaskControlViewSet,
    TopicProfileViewSet,
)


router = DefaultRouter()
router.register(r"sources", CrawlerSourceViewSet, basename="crawler-sources")
router.register(r"topics", TopicProfileViewSet, basename="crawler-topics")
router.register(r"tasks", CrawlerTaskControlViewSet, basename="crawler-tasks-control")
router.register(r"runs", CrawlerRunViewSet, basename="crawler-runs")
router.register(r"items", CrawledItemViewSet, basename="crawler-items")


urlpatterns = [
    path("", include(router.urls)),
]

