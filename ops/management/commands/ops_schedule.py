from django.core.management.base import BaseCommand
from django_q.models import Schedule

SCHEDULE_NAME = "ops: backup and cleanup"
SCHEDULE_FUNC = "ops.maintenance.run_daily"


class Command(BaseCommand):
    """Register the daily backup and cleanup job. Idempotent."""

    help = "Register the recurring backup and cleanup job"

    def handle(self, *args, **options):
        schedule, created = Schedule.objects.update_or_create(
            name=SCHEDULE_NAME,
            defaults={
                "func": SCHEDULE_FUNC,
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{'registered' if created else 'already registered'}: {schedule.name}"
            )
        )
