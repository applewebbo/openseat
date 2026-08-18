from django.core.management.base import BaseCommand

from accounts.groups import EDITORS, ensure_editor_group


class Command(BaseCommand):
    """Create the role groups, or reset them to their definition. Idempotent."""

    help = "Create the role groups the admin reads"

    def handle(self, *args, **options):
        group = ensure_editor_group()
        self.stdout.write(
            self.style.SUCCESS(f"{EDITORS}: {group.permissions.count()} permissions")
        )
