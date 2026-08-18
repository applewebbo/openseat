from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.models import Schedule

SCHEDULE_NAME = "events: pre-event checklist"
SCHEDULE_FUNC = "events.checklist.send_due_checklists"


class Command(BaseCommand):
    """Register the nightly checklist job. Idempotent.

    Fires just after midnight so the list is in somebody's hands before the day
    of the event begins, which is the whole point of it.
    """

    help = "Register the nightly pre-event checklist job"

    def handle(self, *args, **options):
        midnight = (timezone.localtime() + timedelta(days=1)).replace(
            hour=0, minute=5, second=0, microsecond=0
        )
        schedule, created = Schedule.objects.update_or_create(
            name=SCHEDULE_NAME,
            defaults={
                "func": SCHEDULE_FUNC,
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
                "next_run": midnight,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{'registered' if created else 'already registered'}: {schedule.name}"
            )
        )
