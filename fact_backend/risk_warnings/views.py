from rest_framework import viewsets

from .models import RiskWarning
from .serializers import RiskWarningSerializer


class RiskWarningViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MVP：风险预警列表/详情（只读）。
    """

    queryset = (
        RiskWarning.objects.select_related("opinion", "analysis_result")
        .all()
        .order_by("-created_at")
    )
    serializer_class = RiskWarningSerializer

