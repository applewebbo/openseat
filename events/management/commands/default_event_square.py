from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from events.images import square_bytes

WIDE = "img/event-default-wide.jpg"
SQUARE = "img/event-default-square.jpg"


class Command(BaseCommand):
    help = "Cut the square default event picture out of the wide one"

    def add_arguments(self, parser):
        parser.add_argument("--wide", default=None)
        parser.add_argument("--square", default=None)

    def handle(self, *args, **options):
        static_dir = Path(settings.BASE_DIR) / "static"
        wide = Path(options["wide"] or static_dir / WIDE)
        square = Path(options["square"] or static_dir / SQUARE)

        if not wide.exists():
            raise CommandError(f"no wide default picture at {wide}")

        with wide.open("rb") as handle:
            square.write_bytes(square_bytes(handle))

        self.stdout.write(self.style.SUCCESS(f"written: {square}"))
