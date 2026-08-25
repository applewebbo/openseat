"""Demo content, so a fresh clone shows a full home page instead of an empty one.

Everything here is example data for development: the association is real and its
description follows what it publishes about itself, but the dates, the events and
the contact details are made up. Nothing in here belongs in production.
"""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Booking, Event, FeeMethod
from intake.models import Association, PublicForm
from members.models import Member

ASSOCIATION = {
    "slug": "lontano-la-ca-di-asu",
    "name": "L'Ontano - La Ca' di Asu APS",
    "street": "Via Delle Scuole 16",
    "postcode": "28100",
    "city": "Novara",
    "tax_code": "94026180029",
    "email": "segreteria@example.org",
    "statute_url": "https://www.lacadiasu.it/chi-siamo/",
    "membership_fee": 10,
    "home_title": "Un branco di asini, e un modo diverso di stare insieme",
    "home_description": (
        "<p>Ospitiamo un allegro branco di asini e una bardotta, e proponiamo "
        "attività assistite, educative e terapeutiche a diretto contatto con loro. "
        "Lavoriamo su progetti centrati sulla persona nella sua interezza, dove il "
        "legame fra persone, natura e animali è il mezzo e non il contorno.</p>"
        "<p>Siamo nati nel 2003 con l'educazione ambientale e negli anni ci siamo "
        "spostati verso l'ambito sociale, specializzandoci negli Interventi Assistiti "
        "con gli Animali. Gli asini, che molti immaginano testardi, si sono rivelati "
        "i migliori insegnanti che potessimo avere.</p>"
        "<p>Ci trovate negli spazi verdi della Ca' di Asu, a Olengo, frazione di "
        "Novara. Operatori formati in IAA "
        "accompagnano bambini, ragazzi, adulti e anziani.</p>"
    ),
}

# Days from today, so the page always has a next date and a filled archive.
EVENTS = [
    {
        "slug": "giornata-con-gli-asini",
        "title": "Una giornata con gli asini",
        "days": 12,
        "hour": 10,
        "location": "Ca' di Asu, Olengo",
        "description": (
            "Mattina in compagnia del branco: governo degli asini, passeggiata "
            "nel parco e merenda insieme. Per famiglie con bambini dai 4 anni."
        ),
    },
    {
        "slug": "un-basto-carico-di-emozioni",
        "title": "Un basto carico di emozioni",
        "days": 40,
        "hour": 15,
        "location": "Ca' di Asu, Olengo",
        "description": (
            "Laboratorio pomeridiano per genitori e figli, condotto dagli "
            "operatori IAA. Posti limitati dal numero degli asini, non dalla sala."
        ),
    },
    {
        "slug": "porte-aperte-a-ca-di-asu",
        "title": "Porte aperte a Ca' di Asu",
        "days": -21,
        "hour": 10,
        "location": "Ca' di Asu, Olengo",
        "description": "Visita libera al parco e presentazione delle attività dell'anno.",
    },
    {
        "slug": "passeggiata-dautunno",
        "title": "Passeggiata d'autunno con gli asini",
        "days": -68,
        "hour": 14,
        "location": "Ca' di Asu, Olengo",
        "description": "Anello di cinque chilometri lungo la roggia, con soste.",
    },
    {
        "slug": "gli-amici-ritrovati",
        "title": "Gli amici ritrovati",
        "days": -120,
        "hour": 16,
        "location": "Ca' di Asu, Olengo",
        "description": "Incontro conclusivo del progetto, aperto alle famiglie.",
    },
]

# A pool wide enough that each event's roster overlaps but is not identical —
# the same regulars turning up to different dates, as a real register would show.
MEMBERS = [
    {"first_name": "Giulia", "last_name": "Bianchi", "tax_code": "BNCGLI85M41H501Z"},
    {"first_name": "Marco", "last_name": "Rossi", "tax_code": "RSSMRC79A01F205W"},
    {"first_name": "Chiara", "last_name": "Ferrari", "tax_code": "FRRCHR90D55D969X"},
    {"first_name": "Luca", "last_name": "Colombo", "tax_code": "CLMLCU82P15F704Y"},
    {"first_name": "Sara", "last_name": "Ricci", "tax_code": "RCCSRA93T50G273K"},
    {"first_name": "Davide", "last_name": "Marino", "tax_code": "MRNDVD88C12L219H"},
    {"first_name": "Elena", "last_name": "Greco", "tax_code": "GRCLNE91R41E958J"},
    {"first_name": "Andrea", "last_name": "Bruno", "tax_code": "BRNNDR84L05B157G"},
    {"first_name": "Francesca", "last_name": "Gallo", "tax_code": "GLLFNC87S45L840F"},
    {"first_name": "Simone", "last_name": "Conti", "tax_code": "CNTSMN80A19A944D"},
    {"first_name": "Valentina", "last_name": "De Luca", "tax_code": "DLCVNT94M52F839E"},
    {"first_name": "Matteo", "last_name": "Costa", "tax_code": "CSTMTT86H09D542C"},
    {"first_name": "Alessia", "last_name": "Fontana", "tax_code": "FNTLSS92B60G478B"},
    {"first_name": "Riccardo", "last_name": "Barbieri", "tax_code": "BRBRCR81T25H501A"},
    {"first_name": "Martina", "last_name": "Santoro", "tax_code": "SNTMTN95C46F205V"},
    {"first_name": "Nicola", "last_name": "Mariani", "tax_code": "MRNNCL83D14L219U"},
    {"first_name": "Alice", "last_name": "Rinaldi", "tax_code": "RNLLCA89E48E958T"},
    {"first_name": "Federico", "last_name": "Caruso", "tax_code": "CRSFRC77M22B157S"},
    {"first_name": "Silvia", "last_name": "Ferrara", "tax_code": "FRRSLV96A54D969R"},
    {"first_name": "Tommaso", "last_name": "Longo", "tax_code": "LNGTMS90P03F704Q"},
]


class Command(BaseCommand):
    help = "Create example association, form and events for development"

    def handle(self, *args, **options):
        # One installation, one association: an existing one is filled in, never
        # duplicated, and text somebody already wrote is left alone.
        association = Association.current()
        if association is None:
            association = Association.objects.create(**ASSOCIATION)
            self.stdout.write(f"created: {association.name}")
        else:
            missing = {
                field: ASSOCIATION[field]
                for field in ("home_title", "home_description")
                if not getattr(association, field)
            }
            for field, value in missing.items():
                setattr(association, field, value)
            association.save()
            self.stdout.write(
                f"kept: {association.name}"
                + (f" (filled in {', '.join(missing)})" if missing else "")
            )

        public_form, created = PublicForm.objects.get_or_create(
            association=association,
            slug="adesione",
            defaults={
                "title": "Richiesta di adesione",
                "intro": (
                    "Compila il modulo per associarti e prenotare il tuo posto. "
                    "Ti bastano pochi minuti."
                ),
            },
        )
        if created:
            public_form.install_sections()
        self.stdout.write(f"{'created' if created else 'kept'}: {public_form.title}")

        members = []
        for spec in MEMBERS:
            slug = spec["tax_code"]
            email = f"{spec['first_name']}.{spec['last_name']}@example.com".lower()
            member, _created = Member.objects.get_or_create(
                association=association,
                tax_code=slug,
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "contact_name": f"{spec['first_name']} {spec['last_name']}",
                    "contact_email": email,
                    "contact_phone": "3331234567",
                },
            )
            members.append(member)
        self.stdout.write(f"kept: {len(members)} demo members")

        midnight = timezone.localtime().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        for index, spec in enumerate(EVENTS):
            starts_at = midnight + datetime.timedelta(
                days=spec["days"], hours=spec["hour"]
            )
            event, created = Event.objects.update_or_create(
                slug=spec["slug"],
                defaults={
                    "association": association,
                    "form": public_form,
                    "title": spec["title"],
                    "description": spec["description"],
                    "location": spec["location"],
                    "starts_at": starts_at,
                    "ends_at": starts_at + datetime.timedelta(hours=3),
                    "is_published": True,
                },
            )
            self.stdout.write(f"{'created' if created else 'updated'}: {event}")

            # A different, overlapping slice of the pool per event, the way the
            # same regulars turn up to different dates.
            roster_size = 10 + (index % 6)
            start = (index * 4) % len(members)
            roster = [
                members[(start + offset) % len(members)]
                for offset in range(roster_size)
            ]
            booked = 0
            for position, member in enumerate(roster):
                booking = Booking.objects.book(event, member)
                # Roughly a third already confirmed and paid, so the check-in
                # roster shows a realistic mix rather than an all-or-nothing list.
                if position % 3 == 0 and booking.confirmed_on is None:
                    booking.confirmed_on = starts_at.date()
                    booking.fee_amount = association.membership_fee
                    booking.fee_method = FeeMethod.CASH
                    booking.save(
                        update_fields=["confirmed_on", "fee_amount", "fee_method"]
                    )
                booked += 1
            self.stdout.write(f"  booked: {booked} places")

        self.stdout.write(
            self.style.SUCCESS("demo content ready — this is example data")
        )
