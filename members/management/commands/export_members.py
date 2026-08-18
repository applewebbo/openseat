from datetime import date

from django.core.management.base import BaseCommand

from members.export import write_csv
from members.models import Member


class Command(BaseCommand):
    """Write the register, or a slice of it, as CSV.

    The range is by joining date, so the organiser can export after entering the
    paper applications collected on the day of an event without having to
    remember when they last exported.
    """

    help = "Export members who joined within a date range to CSV"

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="since", type=date.fromisoformat)
        parser.add_argument("--to", dest="until", type=date.fromisoformat)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        members = Member.objects.all()
        if options["since"]:
            members = members.filter(joined_on__gte=options["since"])
        if options["until"]:
            members = members.filter(joined_on__lte=options["until"])

        with open(options["output"], "w", newline="", encoding="utf-8") as handle:
            written = write_csv(handle, members)

        self.stdout.write(
            self.style.SUCCESS(f"{written} members written to {options['output']}")
        )
