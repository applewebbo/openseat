from django.core.management.base import BaseCommand

from events.checklist import send_due_checklists


class Command(BaseCommand):
    help = "Send the booking checklist for every event starting today"

    def handle(self, *args, **options):
        sent = send_due_checklists()
        self.stdout.write(self.style.SUCCESS(f"{sent} checklists sent"))
