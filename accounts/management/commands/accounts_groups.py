from django.core.management.base import BaseCommand

from accounts.groups import (
    EDITORS,
    SENIOR_EDITORS,
    ensure_editor_group,
    ensure_senior_editor_group,
)


class Command(BaseCommand):
    """Create the role groups, or reset them to their definition. Idempotent."""

    help = "Create the role groups the admin reads"

    def handle(self, *args, **options):
        for name, group in (
            (EDITORS, ensure_editor_group()),
            (SENIOR_EDITORS, ensure_senior_editor_group()),
        ):
            self.stdout.write(
                self.style.SUCCESS(f"{name}: {group.permissions.count()} permissions")
            )
