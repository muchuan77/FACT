from rest_framework.response import Response
from rest_framework.views import APIView

from analysis.models import AnalysisResult
from opinions.models import OpinionData
from risk_warnings.models import RiskWarning


class DashboardSummaryView(APIView):
    """
    数据大屏统计摘要（MVP 版本）。
    后续可扩展：按时间窗口统计、按来源/类别统计、风险趋势等。
    """

    def get(self, request):
        total_opinions = OpinionData.objects.count()
        analyzed_count = AnalysisResult.objects.count()
        warning_count = RiskWarning.objects.count()
        high_risk_count = RiskWarning.objects.filter(risk_level=RiskWarning.RiskLevel.HIGH).count()

        latest_opinions_qs = OpinionData.objects.order_by("-created_at")[:5]
        latest_warnings_qs = RiskWarning.objects.select_related("opinion").order_by("-created_at")[:5]

        latest_opinion_ids = [o.id for o in latest_opinions_qs]
        latest_analysis_map = {}
        if latest_opinion_ids:
            # SQLite 兼容：不使用 distinct("field")，改为逐条取最新
            for oid in latest_opinion_ids:
                a = AnalysisResult.objects.filter(opinion_id=oid).order_by("-analyzed_at").first()
                if a:
                    latest_analysis_map[oid] = a

        def _merge_keywords(opinion_keywords: list, analysis_keywords: list, limit: int = 8) -> list[str]:
            merged: list[str] = []
            for k in (opinion_keywords or []):
                if isinstance(k, str):
                    kk = k.strip()
                    if kk and kk not in merged:
                        merged.append(kk)
            for k in (analysis_keywords or []):
                if isinstance(k, str):
                    kk = k.strip()
                    if kk and kk not in merged:
                        merged.append(kk)
            return merged[:limit]

        latest_opinions = [
            {
                "id": o.id,
                "title": o.title,
                "source": o.source,
                "status": o.status,
                "keywords": o.keywords,
                "display_keywords": _merge_keywords(
                    o.keywords,
                    (latest_analysis_map.get(o.id).keywords if latest_analysis_map.get(o.id) else []),
                ),
                "created_at": o.created_at,
            }
            for o in latest_opinions_qs
        ]

        latest_warnings = [
            {
                "id": w.id,
                "opinion_id": w.opinion_id,
                "opinion_title": w.opinion.title if w.opinion_id else "",
                "risk_level": w.risk_level,
                "risk_score": w.risk_score,
                "status": w.status,
                "created_at": w.created_at,
            }
            for w in latest_warnings_qs
        ]

        return Response(
            {
                "total_opinions": total_opinions,
                "analyzed_count": analyzed_count,
                "warning_count": warning_count,
                "high_risk_count": high_risk_count,
                "latest_opinions": latest_opinions,
                "latest_warnings": latest_warnings,
            }
        )

