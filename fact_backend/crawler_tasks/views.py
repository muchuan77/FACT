from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import List

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from opinions.models import OpinionData

from .models import CrawledItem, CrawlerRun, CrawlerSource, CrawlerTask, TopicProfile
from .serializers import (
    CrawledItemSerializer,
    CrawlerRunSerializer,
    CrawlerSourceSerializer,
    CrawlerTaskSerializer,
    LegacyCrawlerTaskSerializer,
    TopicProfileSerializer,
)


class CrawlerTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    兼容旧接口：/api/crawler-tasks/（只读，不破坏既有 API）。
    """

    queryset = CrawlerTask.objects.all().order_by("-id")
    serializer_class = LegacyCrawlerTaskSerializer


class CrawlerSourceViewSet(viewsets.ModelViewSet):
    queryset = CrawlerSource.objects.all().order_by("-id")
    serializer_class = CrawlerSourceSerializer


class TopicProfileViewSet(viewsets.ModelViewSet):
    queryset = TopicProfile.objects.all().order_by("-id")
    serializer_class = TopicProfileSerializer


class CrawlerTaskControlViewSet(viewsets.ModelViewSet):
    """
    v1.3.0 任务控制中心：创建任务、切换状态、run-now（同步执行 RSS）。
    """

    queryset = CrawlerTask.objects.all().order_by("-id")
    serializer_class = CrawlerTaskSerializer

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        obj: CrawlerTask = self.get_object()
        obj.status = CrawlerTask.Status.RUNNING
        obj.save(update_fields=["status", "updated_at"])
        return Response({"status": "ok", "task_id": obj.id, "task_status": obj.status})

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        obj: CrawlerTask = self.get_object()
        obj.status = CrawlerTask.Status.PAUSED
        obj.save(update_fields=["status", "updated_at"])
        return Response({"status": "ok", "task_id": obj.id, "task_status": obj.status})

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        obj: CrawlerTask = self.get_object()
        obj.status = CrawlerTask.Status.RUNNING
        obj.save(update_fields=["status", "updated_at"])
        return Response({"status": "ok", "task_id": obj.id, "task_status": obj.status})

    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        obj: CrawlerTask = self.get_object()
        obj.status = CrawlerTask.Status.STOPPED
        obj.save(update_fields=["status", "updated_at"])
        return Response({"status": "ok", "task_id": obj.id, "task_status": obj.status})

    def _collect_task_keywords(self, task: CrawlerTask) -> List[str]:
        if task.task_type == CrawlerTask.TaskType.MONITOR and task.topic_profile:
            return list(task.topic_profile.keywords or [])
        # search 或 monitor 的 override
        if task.keywords:
            return list(task.keywords or [])
        return []

    @action(detail=True, methods=["post"], url_path="run-now")
    def run_now(self, request, pk=None):
        """
        同步执行一次任务（本轮仅执行 RSS + rss_feedparser 适配器）。
        结构上预留后续 Celery/beat：这里只做同步 run-now MVP。
        """
        task: CrawlerTask = self.get_object()
        if task.status in (CrawlerTask.Status.PAUSED, CrawlerTask.Status.STOPPED):
            return Response(
                {"status": "error", "detail": f"task status={task.status} cannot run-now"},
                status=status.HTTP_409_CONFLICT,
            )

        dry_run = bool(request.data.get("dry_run")) if isinstance(request.data, dict) else False

        run = CrawlerRun.objects.create(task=task, status=CrawlerRun.Status.RUNNING)
        started_at = timezone.now()

        # Ensure repo root on sys.path so we can import fact_crawler package.
        repo_root = Path(__file__).resolve().parents[2]
        if str(repo_root) not in sys.path:
            sys.path.append(str(repo_root))

        try:
            enabled_sources = list(task.sources.filter(enabled=True).all())
            rss_sources = [
                s
                for s in enabled_sources
                if s.source_type == CrawlerSource.SourceType.RSS and s.adapter_name == "rss_feedparser"
            ]

            # only support RSS in v1.3.0
            if not rss_sources:
                run.status = CrawlerRun.Status.FAILED
                run.finished_at = timezone.now()
                run.error_message = "no enabled rss sources with adapter rss_feedparser"
                run.save()
                return Response({"status": "failed", "run_id": run.id, "error": run.error_message}, status=400)

            keywords = self._collect_task_keywords(task)
            exclude = list(task.topic_profile.exclude_keywords or []) if task.topic_profile else []
            risk_words = list(task.topic_profile.risk_words or []) if task.topic_profile else []

            from fact_crawler.crawler.runner import run_task_once  # type: ignore

            fetched_total = 0
            valid_total = 0
            inserted_total = 0
            dup_total = 0

            for src in rss_sources:
                items = run_task_once(
                    source_name=src.name,
                    adapter_name=src.adapter_name,
                    base_url=src.base_url,
                    task_type=task.task_type,
                    keywords=keywords,
                    exclude_keywords=exclude,
                    risk_words=risk_words,
                    category=(task.topic_profile.category if task.topic_profile else ""),
                    max_items=task.max_items_per_run,
                )
                fetched_total += len(items)

                for it in items:
                    # dedup by url + content
                    url_hash = CrawledItem.sha256_hex(it.source_url or "")
                    content_hash = CrawledItem.sha256_hex(it.content or "")

                    if CrawledItem.objects.filter(source_url_hash=url_hash).exists() or (
                        content_hash and CrawledItem.objects.filter(content_hash=content_hash).exists()
                    ):
                        dup_total += 1
                        CrawledItem.objects.create(
                            task=task,
                            run=run,
                            title=it.title,
                            content=it.content,
                            source=it.source,
                            source_url=it.source_url,
                            publish_time=it.publish_time,
                            category=it.category,
                            keywords=it.keywords,
                            content_hash=content_hash,
                            source_url_hash=url_hash,
                            status=CrawledItem.Status.DUPLICATE,
                        )
                        continue

                    valid_total += 1

                    crawled = CrawledItem.objects.create(
                        task=task,
                        run=run,
                        title=it.title,
                        content=it.content,
                        source=it.source,
                        source_url=it.source_url,
                        publish_time=it.publish_time,
                        category=it.category,
                        keywords=it.keywords,
                        content_hash=content_hash,
                        source_url_hash=url_hash,
                        status=CrawledItem.Status.NEW,
                    )

                    if dry_run:
                        continue

                    # create OpinionData via ORM (within backend). We keep API-based client in fact_crawler for future use.
                    op = OpinionData.objects.create(
                        title=it.title,
                        content=it.content,
                        source=it.source,
                        source_url=it.source_url,
                        publish_time=it.publish_time,
                        category=it.category,
                        keywords=it.keywords,
                        raw_label="crawler",
                    )
                    crawled.opinion_id = op.id
                    crawled.status = CrawledItem.Status.INSERTED
                    crawled.save(update_fields=["opinion_id", "status"])
                    inserted_total += 1

                    if task.auto_analyze:
                        # call internal analyze endpoint by importing viewset action would be heavy; simplest: hit local API
                        from opinions.views import OpinionDataViewSet  # type: ignore
                        from rest_framework.test import APIRequestFactory  # type: ignore

                        rf = APIRequestFactory()
                        req = rf.post(f"/api/opinions/{op.id}/analyze/", data={})
                        # bind request to view
                        view = OpinionDataViewSet.as_view({"post": "analyze"})
                        _ = view(req, pk=str(op.id))

            run.total_fetched = fetched_total
            run.total_valid = valid_total
            run.total_inserted = inserted_total if not dry_run else 0
            run.total_duplicated = dup_total
            run.status = CrawlerRun.Status.SUCCESS
            run.finished_at = timezone.now()
            run.save()

            task.status = CrawlerTask.Status.FINISHED
            task.save(update_fields=["status", "updated_at"])

            return Response(
                {
                    "status": "ok",
                    "task_id": task.id,
                    "run_id": run.id,
                    "dry_run": dry_run,
                    "total_fetched": fetched_total,
                    "total_valid": valid_total,
                    "total_inserted": inserted_total if not dry_run else 0,
                    "total_duplicated": dup_total,
                }
            )
        except Exception as e:
            run.status = CrawlerRun.Status.FAILED
            run.finished_at = timezone.now()
            run.error_message = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            run.save()
            task.status = CrawlerTask.Status.FAILED
            task.save(update_fields=["status", "updated_at"])
            return Response({"status": "failed", "run_id": run.id, "error": str(e)}, status=500)

    @action(detail=True, methods=["get"], url_path="runs")
    def runs(self, request, pk=None):
        task: CrawlerTask = self.get_object()
        qs = task.runs.order_by("-id")
        page = self.paginate_queryset(qs)
        ser = CrawlerRunSerializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)


class CrawlerRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CrawlerRun.objects.all().order_by("-id")
    serializer_class = CrawlerRunSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        task_id = self.request.query_params.get("task_id")
        if task_id:
            return qs.filter(task_id=task_id)
        return qs

    @action(detail=True, methods=["get"], url_path="items")
    def items(self, request, pk=None):
        run: CrawlerRun = self.get_object()
        qs = run.items.order_by("-id")
        page = self.paginate_queryset(qs)
        ser = CrawledItemSerializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)


class CrawledItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CrawledItem.objects.all().order_by("-id")
    serializer_class = CrawledItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        run_id = self.request.query_params.get("run_id")
        if run_id:
            qs = qs.filter(run_id=run_id)
        return qs

