from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GovernanceRecordViewSet


router = DefaultRouter()
router.register(r"governance", GovernanceRecordViewSet, basename="governance")

urlpatterns = [
    path("", include(router.urls)),
]

