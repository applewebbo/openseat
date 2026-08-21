from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.models import Schedule

SCHEDULE_NAME = "events: pre-event checklist"
SCHEDULE_FUNC = "events.checklist.send_due_checklists"
SWEEP_NAME = "events: unconfirmed booking sweep"
SWEEP_FUNC = "events.maintenance.purge_stale_bookings"


class Command(BaseCommand):
    """Register the nightly checklist job and the booking sweep. Idempotent.

    The checklist fires just after midnight so the list is in somebody's hands
    before the day of the event begins, which is the whole point of it. The
    sweep runs daily too: there is no reason it needs to be prompt.
    """

    help = "Register the nightly pre-event checklist and booking sweep jobs"

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
        sweep, sweep_created = Schedule.objects.update_or_create(
            name=SWEEP_NAME,
            defaults={
                "func": SWEEP_FUNC,
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{'registered' if sweep_created else 'already registered'}: {sweep.name}"
            )
        )
