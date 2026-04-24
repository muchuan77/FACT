from rest_framework import viewsets

from .models import GovernanceRecord
from .serializers import GovernanceRecordSerializer


class GovernanceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MVP：治理响应记录列表/详情（只读）。
    """

    queryset = GovernanceRecord.objects.select_related("warning").all().order_by("-created_at")
    serializer_class = GovernanceRecordSerializer

