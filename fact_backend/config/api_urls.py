from django.urls import include, path
from rest_framework.routers import DefaultRouter

from analysis.views import AnalysisResultViewSet
from crawler_tasks.views import CrawlerTaskViewSet
from governance.views import GovernanceRecordViewSet
from model_versions.views import ModelVersionViewSet
from opinions.views import OpinionDataViewSet
from risk_warnings.views import RiskWarningViewSet
from .views import DashboardSummaryView


router = DefaultRouter()
router.register(r"opinions", OpinionDataViewSet, basename="opinions")
router.register(r"analysis", AnalysisResultViewSet, basename="analysis")
router.register(r"warnings", RiskWarningViewSet, basename="warnings")
router.register(r"governance", GovernanceRecordViewSet, basename="governance")
router.register(r"crawler-tasks", CrawlerTaskViewSet, basename="crawler-tasks")
router.register(r"model-versions", ModelVersionViewSet, basename="model-versions")

urlpatterns = [
    path("", include(router.urls)),
    path("users/", include("users.urls")),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("crawler/", include("crawler_tasks.crawler_urls")),
]

