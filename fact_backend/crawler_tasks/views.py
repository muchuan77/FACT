from rest_framework import viewsets

from .models import CrawlerTask
from .serializers import CrawlerTaskSerializer


class CrawlerTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MVP：爬虫任务记录列表/详情（只读）。
    """

    queryset = CrawlerTask.objects.all().order_by("-id")
    serializer_class = CrawlerTaskSerializer

