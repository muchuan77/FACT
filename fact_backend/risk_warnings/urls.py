from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RiskWarningViewSet


router = DefaultRouter()
router.register(r"warnings", RiskWarningViewSet, basename="warnings")

urlpatterns = [
    path("", include(router.urls)),
]

