from rest_framework import viewsets

from .models import ModelVersion
from .serializers import ModelVersionSerializer


class ModelVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MVP：模型版本列表/详情（只读）。
    """

    queryset = ModelVersion.objects.all().order_by("-created_at")
    serializer_class = ModelVersionSerializer

