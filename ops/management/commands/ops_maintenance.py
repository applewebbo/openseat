from django.core.management.base import BaseCommand

from ops.maintenance import delete_orphan_media, purge_old_backups


class Command(BaseCommand):
    """Delete expired backups and media nothing references any more."""

    help = "Purge expired backups and orphaned media files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List what would be deleted without touching anything",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        for name in purge_old_backups(dry_run=dry_run):
            self.stdout.write(f"backup    {name}")
        for name in delete_orphan_media(dry_run=dry_run):
            self.stdout.write(f"media     {name}")
        self.stdout.write(
            self.style.WARNING("dry run: nothing was deleted")
            if dry_run
            else self.style.SUCCESS("done")
        )
