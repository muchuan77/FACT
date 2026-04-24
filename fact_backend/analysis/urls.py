from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnalysisResultViewSet


router = DefaultRouter()
router.register(r"analysis", AnalysisResultViewSet, basename="analysis")

urlpatterns = [
    path("", include(router.urls)),
]

