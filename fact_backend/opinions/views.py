from __future__ import annotations

from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import OpinionData
from .serializers import OpinionDataSerializer


class OpinionDataViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    MVP：舆情数据列表/新增/详情。
    """

    queryset = OpinionData.objects.all().order_by("-created_at")
    serializer_class = OpinionDataSerializer

    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request, pk=None):
        """
        最小业务闭环接口：对指定舆情进行模型分析并生成风险预警。

        POST /api/opinions/{id}/analyze/
        """
        opinion: OpinionData = self.get_object()  # DRF: 自动 404
        text = (opinion.content or "").strip()
        if not text:
            return Response(
                {"detail": "OpinionData.content 为空，无法分析"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from analysis.models import AnalysisResult
        from analysis.serializers import AnalysisResultSerializer
        from risk_warnings.models import RiskWarning
        from risk_warnings.serializers import RiskWarningSerializer

        def _merge_keywords(model_keywords: list, opinion_keywords: list) -> list[str]:
            merged: list[str] = []
            for k in (model_keywords or []):
                if isinstance(k, str):
                    kk = k.strip()
                    if kk and kk not in merged:
                        merged.append(kk)
            for k in (opinion_keywords or []):
                if isinstance(k, str):
                    kk = k.strip()
                    if kk and kk not in merged:
                        merged.append(kk)
            return merged

        # 幂等：如果已存在分析结果与预警结果，则直接复用（不重复插入）
        existing_analysis = (
            AnalysisResult.objects.filter(opinion=opinion).order_by("-analyzed_at").first()
        )
        existing_warning = (
            RiskWarning.objects.filter(opinion=opinion).order_by("-created_at").first()
        )
        if existing_analysis and existing_warning:
            # 幂等补齐：若分析结果 keywords 为空，但舆情 keywords 不为空，则补齐并返回
            if not (existing_analysis.keywords or []) and (opinion.keywords or []):
                existing_analysis.keywords = _merge_keywords([], opinion.keywords)
                existing_analysis.save(update_fields=["keywords"])
            # 同步回写：若分析结果有关键词但舆情 keywords 为空，则回写到 OpinionData.keywords
            if (existing_analysis.keywords or []) and not (opinion.keywords or []):
                opinion.keywords = _merge_keywords([], existing_analysis.keywords)[:8]
                opinion.save(update_fields=["keywords", "updated_at"])
            return Response(
                {
                    "opinion": OpinionDataSerializer(opinion).data,
                    "analysis_result": AnalysisResultSerializer(existing_analysis).data,
                    "risk_warning": RiskWarningSerializer(existing_warning).data,
                    "note": "already analyzed; returned existing records",
                },
                status=status.HTTP_200_OK,
            )

        if existing_analysis and not existing_warning:
            # 只补齐预警，不重复创建分析结果
            if not (existing_analysis.keywords or []) and (opinion.keywords or []):
                existing_analysis.keywords = _merge_keywords([], opinion.keywords)
                existing_analysis.save(update_fields=["keywords"])
            if (existing_analysis.keywords or []) and not (opinion.keywords or []):
                opinion.keywords = _merge_keywords([], existing_analysis.keywords)[:8]
                opinion.save(update_fields=["keywords", "updated_at"])
            rumor_probability = float(existing_analysis.rumor_probability or 0.0)
            sentiment_probability = float(existing_analysis.sentiment_probability or 0.0)
            risk_score = (rumor_probability + sentiment_probability) / 2.0
            if risk_score >= 0.75:
                risk_level = RiskWarning.RiskLevel.HIGH
            elif risk_score >= 0.45:
                risk_level = RiskWarning.RiskLevel.MEDIUM
            else:
                risk_level = RiskWarning.RiskLevel.LOW

            warning_reason = (
                f"risk_score={risk_score:.2f}, rumor={rumor_probability:.2f}, sentiment={sentiment_probability:.2f}"
            )
            with transaction.atomic():
                warning = RiskWarning.objects.create(
                    opinion=opinion,
                    analysis_result=existing_analysis,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    warning_reason=warning_reason,
                )

                if risk_level in (RiskWarning.RiskLevel.HIGH, RiskWarning.RiskLevel.MEDIUM):
                    opinion.status = OpinionData.Status.WARNED
                else:
                    opinion.status = OpinionData.Status.ANALYZED
                opinion.save(update_fields=["status", "updated_at"])

            return Response(
                {
                    "opinion": OpinionDataSerializer(opinion).data,
                    "analysis_result": AnalysisResultSerializer(existing_analysis).data,
                    "risk_warning": RiskWarningSerializer(warning).data,
                    "note": "analysis existed; created missing warning",
                },
                status=status.HTTP_200_OK,
            )

        # 首次分析：调用模型服务并落库
        from services.model_client import predict_full

        model_resp = predict_full(text)
        if not isinstance(model_resp, dict) or model_resp.get("error"):
            return Response(
                {
                    "detail": "模型服务不可用或返回异常",
                    "model_service_error": model_resp.get("error") if isinstance(model_resp, dict) else None,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            rumor_label = str(model_resp.get("rumor_label", "") or "")
            rumor_probability = float(model_resp.get("rumor_probability", 0.0) or 0.0)
            sentiment_label = str(model_resp.get("sentiment_label", "") or "")
            sentiment_probability = float(model_resp.get("sentiment_probability", 0.0) or 0.0)
            keywords = model_resp.get("keywords") or []
            if not isinstance(keywords, list):
                keywords = []
            model_name = str(model_resp.get("model_name", "") or "")
        except Exception as exc:
            return Response(
                {"detail": "模型服务返回字段解析失败", "error": str(exc), "raw": model_resp},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 合并关键词：模型返回 keywords + OpinionData.keywords（去重）
        merged_keywords = _merge_keywords(keywords, opinion.keywords)

        # 风险评分（MVP）：简单平均
        risk_score = (rumor_probability + sentiment_probability) / 2.0
        if risk_score >= 0.75:
            risk_level = RiskWarning.RiskLevel.HIGH
        elif risk_score >= 0.45:
            risk_level = RiskWarning.RiskLevel.MEDIUM
        else:
            risk_level = RiskWarning.RiskLevel.LOW

        with transaction.atomic():
            analysis = AnalysisResult.objects.create(
                opinion=opinion,
                rumor_label=rumor_label,
                rumor_probability=rumor_probability,
                sentiment_label=sentiment_label,
                sentiment_probability=sentiment_probability,
                keywords=merged_keywords,
                model_name=model_name,
            )

            # 同步回写：旧数据/未填 keywords 时，将模型分析关键词回写到 OpinionData.keywords
            wrote_back_keywords = False
            if merged_keywords and not (opinion.keywords or []):
                opinion.keywords = merged_keywords[:8]
                wrote_back_keywords = True

            warning_reason = (
                f"risk_score={risk_score:.2f}, rumor={rumor_probability:.2f}, sentiment={sentiment_probability:.2f}"
            )
            warning = RiskWarning.objects.create(
                opinion=opinion,
                analysis_result=analysis,
                risk_score=risk_score,
                risk_level=risk_level,
                warning_reason=warning_reason,
            )

            if risk_level in (RiskWarning.RiskLevel.HIGH, RiskWarning.RiskLevel.MEDIUM):
                opinion.status = OpinionData.Status.WARNED
            else:
                opinion.status = OpinionData.Status.ANALYZED
            # keywords 可能在上方被回写
            fields = ["status", "updated_at"]
            if wrote_back_keywords:
                fields.append("keywords")
            opinion.save(update_fields=list(dict.fromkeys(fields)))

        return Response(
            {
                "opinion": OpinionDataSerializer(opinion).data,
                "analysis_result": AnalysisResultSerializer(analysis).data,
                "risk_warning": RiskWarningSerializer(warning).data,
            },
            status=status.HTTP_200_OK,
        )

