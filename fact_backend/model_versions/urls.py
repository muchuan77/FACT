from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ModelVersionViewSet


router = DefaultRouter()
router.register(r"model-versions", ModelVersionViewSet, basename="model-versions")

urlpatterns = [
    path("", include(router.urls)),
]

