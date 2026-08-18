"""Demo content, so a fresh clone shows a full home page instead of an empty one.

Everything here is example data for development: the association is real and its
description follows what it publishes about itself, but the dates, the events and
the contact details are made up. Nothing in here belongs in production.
"""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event
from intake.models import Association, PublicForm

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
        "<p>Ci trovate negli spazi verdi intorno a Villa Segù, dimora di fine "
        "Settecento a Olengo, frazione di Novara. Operatori formati in IAA "
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
        "location": "Villa Segù, Olengo (NO)",
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
        "location": "Villa Segù, Olengo (NO)",
        "description": (
            "Laboratorio pomeridiano per genitori e figli, condotto dagli "
            "operatori IAA. Posti limitati dal numero degli asini, non dalla sala."
        ),
    },
    {
        "slug": "porte-aperte-a-villa-segu",
        "title": "Porte aperte a Villa Segù",
        "days": -21,
        "hour": 10,
        "location": "Villa Segù, Olengo (NO)",
        "description": "Visita libera al parco e presentazione delle attività dell'anno.",
    },
    {
        "slug": "passeggiata-dautunno",
        "title": "Passeggiata d'autunno con gli asini",
        "days": -68,
        "hour": 14,
        "location": "Cascina Bornago, Novara",
        "description": "Anello di cinque chilometri lungo la roggia, con soste.",
    },
    {
        "slug": "gli-amici-ritrovati",
        "title": "Gli amici ritrovati",
        "days": -120,
        "hour": 16,
        "location": "Villa Segù, Olengo (NO)",
        "description": "Incontro conclusivo del progetto, aperto alle famiglie.",
    },
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

        midnight = timezone.localtime().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        for spec in EVENTS:
            starts_at = midnight + datetime.timedelta(
                days=spec["days"], hours=spec["hour"]
            )
            event, created = Event.objects.update_or_create(
                slug=spec["slug"],
                defaults={
                    "association": association,
                    "title": spec["title"],
                    "description": spec["description"],
                    "location": spec["location"],
                    "starts_at": starts_at,
                    "ends_at": starts_at + datetime.timedelta(hours=3),
                    "is_published": True,
                },
            )
            self.stdout.write(f"{'created' if created else 'updated'}: {event}")

        self.stdout.write(
            self.style.SUCCESS("demo content ready — this is example data")
        )
