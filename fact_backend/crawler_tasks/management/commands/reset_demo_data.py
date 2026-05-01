from __future__ import annotations

from django.core.management.base import BaseCommand

from analysis.models import AnalysisResult
from crawler_tasks.models import CrawledItem, CrawlerRun, CrawlerSource, CrawlerTask, TopicProfile
from governance.models import GovernanceRecord
from opinions.models import OpinionData
from risk_warnings.models import RiskWarning


class Command(BaseCommand):
    help = "Reset demo/test data (development only). Use --yes to actually delete."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Confirm deletion (required).")

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

