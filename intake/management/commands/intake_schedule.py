from django.core.management.base import BaseCommand
from django_q.models import Schedule

SCHEDULE_NAME = "intake: draft maintenance"
SCHEDULE_FUNC = "intake.maintenance.run_draft_maintenance"


class Command(BaseCommand):
    """Register the hourly sweep that reminds and expires drafts.

    Idempotent, and run from entrypoint.sh next to migrate: a data migration
    would be invisible to a suite that builds its schema with --nomigrations.
    The thresholds live in settings; this only sets how often they are checked.
    """

    help = "Register the recurring draft maintenance job"

    def handle(self, *args, **options):
        schedule, created = Schedule.objects.update_or_create(
            name=SCHEDULE_NAME,
            defaults={
                "func": SCHEDULE_FUNC,
                "schedule_type": Schedule.HOURLY,
                "repeats": -1,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{'registered' if created else 'already registered'}: {schedule.name}"
            )
        )
