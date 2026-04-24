from rest_framework import viewsets

from .models import AnalysisResult
from .serializers import AnalysisResultSerializer


class AnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MVP：分析结果列表/详情（只读）。
    """

    queryset = AnalysisResult.objects.select_related("opinion").all().order_by("-analyzed_at")
    serializer_class = AnalysisResultSerializer

