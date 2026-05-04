from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection

from analysis.models import AnalysisResult
from crawler_tasks.models import CrawledItem, CrawlerRun, CrawlerSource, CrawlerTask, TopicProfile
from governance.models import GovernanceRecord
from opinions.models import OpinionData
from risk_warnings.models import RiskWarning


class Command(BaseCommand):
    help = "Reset demo/test data (development only). Use --yes to actually delete."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Confirm deletion (required).")
        parser.add_argument(
            "--reset-sequences",
            action="store_true",
            help="After delete, reset DB auto-increment counters (SQLite only in-repo; dev only).",
        )

    def handle(self, *args, **options):
        if not options.get("yes"):
            self.stdout.write(self.style.WARNING("[DRY] No action taken. Use: python manage.py reset_demo_data --yes"))
            return

        # Delete order to avoid FK issues:
        # RiskWarning -> AnalysisResult -> CrawledItem -> CrawlerRun -> CrawlerTask -> TopicProfile -> CrawlerSource -> OpinionData -> GovernanceRecord
        counts = {}

        counts["RiskWarning"] = RiskWarning.objects.all().delete()[0]
        counts["AnalysisResult"] = AnalysisResult.objects.all().delete()[0]
        counts["CrawledItem"] = CrawledItem.objects.all().delete()[0]
        counts["CrawlerRun"] = CrawlerRun.objects.all().delete()[0]
        counts["CrawlerTask"] = CrawlerTask.objects.all().delete()[0]
        counts["TopicProfile"] = TopicProfile.objects.all().delete()[0]
        counts["CrawlerSource"] = CrawlerSource.objects.all().delete()[0]
        counts["OpinionData"] = OpinionData.objects.all().delete()[0]
        counts["GovernanceRecord"] = GovernanceRecord.objects.all().delete()[0]

        self.stdout.write(self.style.SUCCESS("[OK] reset_demo_data finished. deleted counts:"))
        for k, v in counts.items():
            self.stdout.write(f"- {k}: {v}")

        if options.get("reset_sequences"):
            self._reset_sequences()

    def _reset_sequences(self) -> None:
        vendor = connection.vendor
        if vendor == "sqlite":
            tables = [
                RiskWarning._meta.db_table,
                AnalysisResult._meta.db_table,
                CrawledItem._meta.db_table,
                CrawlerRun._meta.db_table,
                CrawlerTask.sources.through._meta.db_table,
                CrawlerTask._meta.db_table,
                TopicProfile._meta.db_table,
                CrawlerSource._meta.db_table,
                OpinionData._meta.db_table,
                GovernanceRecord._meta.db_table,
            ]
            # 不用 ? 占位符：DEBUG=True 时 SQLite 后端用 sql % params 打印 last_executed_query，
            # 会与 ? 占位符冲突，触发 TypeError: not all arguments converted during string formatting。
            with connection.cursor() as cursor:
                for t in tables:
                    safe = (t or "").replace("'", "''")
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name = '{safe}'")
            self.stdout.write(
                self.style.SUCCESS(
                    "[OK] reset-sequences: cleared sqlite_sequence for crawler_tasks / opinions / "
                    "analysis / risk_warnings / governance related tables (see command source for list)."
                )
            )
            return

        if vendor == "postgresql":
            self.stdout.write(
                self.style.WARNING(
                    "[SKIP] PostgreSQL：未自动重置序列。可在开发库中按需执行 "
                    "`python manage.py sqlsequencereset crawler_tasks opinions ...` 或手写 "
                    "`ALTER SEQUENCE ... RESTART WITH 1`。生产环境请依赖 CrawlerSource.source_code，"
                    "勿依赖自增主键 id。"
                )
            )
            return

        if vendor == "mysql":
            self.stdout.write(
                self.style.WARNING(
                    "[SKIP] MySQL：未自动重置 AUTO_INCREMENT。请在开发库中按需对有关表执行 "
                    "`ALTER TABLE ... AUTO_INCREMENT = 1`（注意外键与空表行为）。"
                    "生产环境请依赖 source_code，勿依赖自增 id。"
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"[SKIP] 当前数据库引擎 {vendor!r} 未实现 --reset-sequences；"
                "生产环境请依赖 CrawlerSource.source_code，勿依赖自增 id。"
            )
        )
