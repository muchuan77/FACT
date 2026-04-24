from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync OpinionData.keywords from latest AnalysisResult.keywords when empty."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Limit number of opinions to process (0 means all).")
        parser.add_argument("--dry-run", action="store_true", help="Do not write changes, only report.")

    def handle(self, *args, **options):
        from analysis.models import AnalysisResult
        from opinions.models import OpinionData

        limit = int(options["limit"] or 0)
        dry_run = bool(options["dry_run"])

        qs = OpinionData.objects.all().order_by("id")
        if limit > 0:
            qs = qs[:limit]

        processed = 0
        updated = 0

        for o in qs:
            processed += 1
            if o.keywords:
                continue
            a = AnalysisResult.objects.filter(opinion=o).order_by("-analyzed_at").first()
            if not a or not a.keywords:
                continue

            new_keywords = []
            for k in a.keywords:
                if isinstance(k, str):
                    kk = k.strip()
                    if kk and kk not in new_keywords:
                        new_keywords.append(kk)
                if len(new_keywords) >= 8:
                    break

            if not new_keywords:
                continue

            updated += 1
            if not dry_run:
                o.keywords = new_keywords
                o.save(update_fields=["keywords", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"processed={processed} updated={updated} dry_run={dry_run}"
            )
        )

