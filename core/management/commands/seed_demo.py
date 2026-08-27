"""Demo content, so a fresh clone shows a full home page instead of an empty one.

Everything here is example data for development: the association is real and its
description follows what it publishes about itself, but the dates, the events and
the contact details are made up. Nothing in here belongs in production.
"""

import datetime

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.groups import ensure_editor_group, ensure_senior_editor_group
from events.models import Booking, Event, FeeMethod
from intake.models import AgeBracket, Association, PublicForm, SubjectType, Submission
from members.models import Member

TEST_USERS = (
    ("editor@example.com", ensure_editor_group),
    ("senior-editor@example.com", ensure_senior_editor_group),
)

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

# The register mirrors real bookings: applying for a child, the association's
# actual majority, so most of the pool is a parent-and-child pair. Confirming
# the booking is what enrols the child — exactly the production path, not a
# shortcut — so a booking left unconfirmed never creates a register entry.
FAMILIES = [
    {
        "parent_first_name": "Giulia",
        "parent_last_name": "Bianchi",
        "parent_email": "giulia.bianchi@example.com",
        "child_first_name": "Sofia",
        "child_last_name": "Bianchi",
        "child_birth_date": "2019-05-11",
    },
    {
        "parent_first_name": "Marco",
        "parent_last_name": "Rossi",
        "parent_email": "marco.rossi@example.com",
        "child_first_name": "Leonardo",
        "child_last_name": "Rossi",
        "child_birth_date": "2013-02-20",
    },
    {
        "parent_first_name": "Chiara",
        "parent_last_name": "Ferrari",
        "parent_email": "chiara.ferrari@example.com",
        "child_first_name": "Emma",
        "child_last_name": "Ferrari",
        "child_birth_date": "2016-09-03",
    },
    {
        "parent_first_name": "Luca",
        "parent_last_name": "Colombo",
        "parent_email": "luca.colombo@example.com",
        "child_first_name": "Tommaso",
        "child_last_name": "Colombo",
        "child_birth_date": "2011-12-14",
    },
    {
        "parent_first_name": "Sara",
        "parent_last_name": "Ricci",
        "parent_email": "sara.ricci@example.com",
        "child_first_name": "Giorgia",
        "child_last_name": "Ricci",
        "child_birth_date": "2012-07-27",
    },
    {
        "parent_first_name": "Davide",
        "parent_last_name": "Marino",
        "parent_email": "davide.marino@example.com",
        "child_first_name": "Riccardo",
        "child_last_name": "Marino",
        "child_birth_date": "2014-04-18",
    },
    {
        "parent_first_name": "Elena",
        "parent_last_name": "Greco",
        "parent_email": "elena.greco@example.com",
        "child_first_name": "Alice",
        "child_last_name": "Greco",
        "child_birth_date": "2017-10-09",
    },
    {
        "parent_first_name": "Andrea",
        "parent_last_name": "Bruno",
        "parent_email": "andrea.bruno@example.com",
        "child_first_name": "Matteo",
        "child_last_name": "Bruno",
        "child_birth_date": "2013-01-30",
    },
    {
        "parent_first_name": "Francesca",
        "parent_last_name": "Gallo",
        "parent_email": "francesca.gallo@example.com",
        "child_first_name": "Vittoria",
        "child_last_name": "Gallo",
        "child_birth_date": "2015-06-06",
    },
    {
        "parent_first_name": "Simone",
        "parent_last_name": "Conti",
        "parent_email": "simone.conti@example.com",
        "child_first_name": "Francesco",
        "child_last_name": "Conti",
        "child_birth_date": "2012-08-22",
    },
    {
        "parent_first_name": "Valentina",
        "parent_last_name": "De Luca",
        "parent_email": "valentina.deluca@example.com",
        "child_first_name": "Aurora",
        "child_last_name": "De Luca",
        "child_birth_date": "2010-03-15",
    },
    {
        "parent_first_name": "Matteo",
        "parent_last_name": "Costa",
        "parent_email": "matteo.costa@example.com",
        "child_first_name": "Diego",
        "child_last_name": "Costa",
        "child_birth_date": "2018-11-02",
    },
    {
        "parent_first_name": "Alessia",
        "parent_last_name": "Fontana",
        "parent_email": "alessia.fontana@example.com",
        "child_first_name": "Beatrice",
        "child_last_name": "Fontana",
        "child_birth_date": "2014-09-19",
    },
    {
        "parent_first_name": "Riccardo",
        "parent_last_name": "Barbieri",
        "parent_email": "riccardo.barbieri@example.com",
        "child_first_name": "Gabriele",
        "child_last_name": "Barbieri",
        "child_birth_date": "2020-01-25",
    },
    {
        "parent_first_name": "Martina",
        "parent_last_name": "Santoro",
        "parent_email": "martina.santoro@example.com",
        "child_first_name": "Camilla",
        "child_last_name": "Santoro",
        "child_birth_date": "2016-05-08",
    },
    {
        "parent_first_name": "Nicola",
        "parent_last_name": "Mariani",
        "parent_email": "nicola.mariani@example.com",
        "child_first_name": "Pietro",
        "child_last_name": "Mariani",
        "child_birth_date": "2021-03-30",
    },
]

# A handful of adults booking for themselves, so the roster is not all minors.
SELF_ADULTS = [
    {
        "first_name": "Federico",
        "last_name": "Caruso",
        "email": "federico.caruso@example.com",
        "birth_date": "1996-01-22",
    },
    {
        "first_name": "Silvia",
        "last_name": "Ferrara",
        "email": "silvia.ferrara@example.com",
        "birth_date": "1978-04-04",
    },
    {
        "first_name": "Tommaso",
        "last_name": "Longo",
        "email": "tommaso.longo@example.com",
        "birth_date": "1962-03-03",
    },
]


# Fifty members entered directly on the register, the way years of paper
# admissions predating this app would look once typed in: no submission or
# booking behind them, a export CSV/xlsx exercised at a realistic size.
STANDALONE_FIRST_NAMES = [
    "Anna",
    "Paolo",
    "Laura",
    "Giovanni",
    "Elisa",
    "Roberto",
    "Federica",
    "Stefano",
    "Michela",
    "Antonio",
    "Cristina",
    "Fabio",
    "Serena",
    "Massimo",
    "Ilaria",
    "Claudio",
    "Barbara",
    "Enrico",
    "Monica",
    "Giorgio",
    "Patrizia",
    "Alberto",
    "Daniela",
    "Vincenzo",
    "Silvia",
    "Renato",
    "Paola",
    "Gianluca",
    "Rosa",
    "Emanuele",
    "Lucia",
    "Marco",
    "Simona",
    "Pietro",
    "Giovanna",
    "Sergio",
    "Manuela",
    "Franco",
    "Alessandra",
    "Carlo",
    "Teresa",
    "Angelo",
    "Raffaella",
    "Mauro",
    "Lorena",
    "Domenico",
    "Wanda",
    "Alessandro",
    "Ornella",
    "Gabriele",
]
STANDALONE_LAST_NAMES = [
    "Riva",
    "Motta",
    "Vitali",
    "Sala",
    "Pirola",
    "Cattaneo",
    "Beretta",
    "Villa",
    "Brambilla",
    "Meroni",
    "Colombo",
    "Locatelli",
    "Vismara",
    "Galbiati",
    "Redaelli",
    "Pozzi",
    "Bonetti",
    "Arosio",
    "Consonni",
    "Riboldi",
    "Perego",
    "Citterio",
    "Vergani",
    "Longoni",
    "Panzeri",
    "Corti",
    "Casati",
    "Mauri",
    "Sironi",
    "Tagliabue",
    "Nava",
    "Colnaghi",
    "Frigerio",
    "Rota",
    "Valsecchi",
    "Airoldi",
    "Gerosa",
    "Spreafico",
    "Ripamonti",
    "Radaelli",
    "Fumagalli",
    "Confalonieri",
    "Bertani",
    "Pagani",
    "Molteni",
    "Sangalli",
    "Oggioni",
    "Crippa",
    "Barzaghi",
    "Terraneo",
]
STANDALONE_ADDRESSES = [
    ("Via Trieste", "4", "28100", "Novara", "NO"),
    ("Via Divisione Julia", "22", "28100", "Novara", "NO"),
    ("Corso Cavallotti", "9", "28100", "Novara", "NO"),
    ("Via Solaroli", "15", "28100", "Novara", "NO"),
    ("Piazza Cavour", "3", "28100", "Novara", "NO"),
    ("Via Perrone", "40", "28047", "Oleggio", "NO"),
    ("Via Roma", "18", "28069", "Trecate", "NO"),
    ("Via Novara", "56", "28053", "Galliate", "NO"),
    ("Via Cameri", "7", "28062", "Cameri", "NO"),
    ("Via Boniperti", "11", "28100", "Olengo", "NO"),
]


def _standalone_members(association, today):
    for index, (first_name, last_name) in enumerate(
        zip(STANDALONE_FIRST_NAMES, STANDALONE_LAST_NAMES, strict=True)
    ):
        street, number, postcode, city, province = STANDALONE_ADDRESSES[
            index % len(STANDALONE_ADDRESSES)
        ]
        birth_year = 1950 + (index * 3) % 55
        joined_on = today - datetime.timedelta(days=(index * 23) % 1800)
        yield {
            "contact_email": f"socio{index + 1}@example.com",
            "first_name": first_name,
            "last_name": last_name,
            "birth_date": datetime.date(birth_year, 1 + index % 12, 1 + index % 28),
            "tax_code": (
                "" if index % 5 == 0 else f"MBR{index:02d}A01H501{index % 10}"
            ),
            "street": street,
            "number": number,
            "postcode": postcode,
            "city": city,
            "province": province,
            "email": f"socio{index + 1}@example.com",
            "contact_name": f"{first_name} {last_name}",
            "contact_phone": f"333{1000000 + index:07d}",
            "joined_on": joined_on,
            "ratified_on": None if index % 3 == 0 else joined_on,
        }


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

        # The migration that seeds these only runs against associations that
        # already existed at migrate time — a fresh DB has none yet, so this
        # command must not assume the bookings summary card has anything to
        # group by.
        if not association.age_brackets.exists():
            AgeBracket.objects.bulk_create(
                [
                    AgeBracket(
                        association=association,
                        label=label,
                        min_age=lo,
                        max_age=hi,
                        order=order,
                    )
                    for order, (label, lo, hi) in enumerate(
                        [
                            ("0-5", 0, 5),
                            ("6-9", 6, 9),
                            ("10-14", 10, 14),
                            ("15-17", 15, 17),
                            ("18+", 18, None),
                        ]
                    )
                ]
            )
            self.stdout.write("created: default age brackets")

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

        # Normalised so the booking loop below does not care whether a slot is
        # a parent applying for a child or an adult applying for themselves.
        pool = []
        for index_, family in enumerate(FAMILIES):
            street, number, postcode, city, _province = STANDALONE_ADDRESSES[
                index_ % len(STANDALONE_ADDRESSES)
            ]
            pool.append(
                {
                    "is_minor": True,
                    "first_name": family["child_first_name"],
                    "last_name": family["child_last_name"],
                    "birth_date": family["child_birth_date"],
                    "applicant_first_name": family["parent_first_name"],
                    "applicant_last_name": family["parent_last_name"],
                    "email": family["parent_email"],
                    "street": street,
                    "number": number,
                    "postcode": postcode,
                    "city": city,
                    "tax_code": f"CHD{index_:02d}A01H501{index_ % 10}",
                }
            )
            # One self-adult sprinkled in every sixth slot: minors stay a
            # comfortable majority (well over 80%) of any roster slice.
            if SELF_ADULTS and (index_ + 1) % 6 == 0:
                adult_index = (index_ + 1) // 6
                adult = SELF_ADULTS[adult_index % len(SELF_ADULTS)]
                pool.append(
                    {
                        "is_minor": False,
                        "first_name": adult["first_name"],
                        "last_name": adult["last_name"],
                        "birth_date": adult["birth_date"],
                        "applicant_first_name": adult["first_name"],
                        "applicant_last_name": adult["last_name"],
                        "email": adult["email"],
                        "street": street,
                        "number": number,
                        "postcode": postcode,
                        "city": city,
                        "tax_code": f"ADU{adult_index:02d}A01H501{adult_index % 10}",
                    }
                )

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
            start = (index * 4) % len(pool)
            roster = [
                pool[(start + offset) % len(pool)] for offset in range(roster_size)
            ]
            booked = 0
            for position, spec_ in enumerate(roster):
                existing = Booking.objects.filter(
                    event=event,
                    first_name=spec_["first_name"],
                    last_name=spec_["last_name"],
                ).first()
                if existing is None:
                    submission = Submission.objects.create(
                        form=public_form,
                        state=Submission.State.SUBMITTED,
                        submitted_at=starts_at - datetime.timedelta(days=10),
                        subject_type=(
                            SubjectType.MINOR if spec_["is_minor"] else SubjectType.SELF
                        ),
                        applicant_first_name=spec_["applicant_first_name"],
                        applicant_last_name=spec_["applicant_last_name"],
                        applicant_birth_date=(
                            None if spec_["is_minor"] else spec_["birth_date"]
                        ),
                        applicant_email=spec_["email"],
                        applicant_phone="3331234567",
                        applicant_street=spec_["street"],
                        applicant_number=spec_["number"],
                        applicant_postcode=spec_["postcode"],
                        applicant_city=spec_["city"],
                        applicant_tax_code=(
                            "" if spec_["is_minor"] else spec_["tax_code"]
                        ),
                        member_first_name=(
                            spec_["first_name"] if spec_["is_minor"] else ""
                        ),
                        member_last_name=(
                            spec_["last_name"] if spec_["is_minor"] else ""
                        ),
                        member_birth_date=(
                            spec_["birth_date"] if spec_["is_minor"] else None
                        ),
                        member_street=(spec_["street"] if spec_["is_minor"] else ""),
                        member_number=(spec_["number"] if spec_["is_minor"] else ""),
                        member_city=(spec_["city"] if spec_["is_minor"] else ""),
                        member_tax_code=(
                            spec_["tax_code"] if spec_["is_minor"] else ""
                        ),
                        accepts_statute=True,
                        sole_holder=True if spec_["is_minor"] else None,
                    )
                    existing = Booking.objects.book_application(event, submission)
                # A fifth already confirmed and paid — most check-ins still
                # happen at the door, not ahead of time.
                if position % 5 == 0 and existing.confirmed_on is None:
                    existing.confirmed_on = starts_at.date()
                    existing.fee_amount = association.membership_fee
                    existing.fee_method = FeeMethod.CASH
                    existing.save(
                        update_fields=["confirmed_on", "fee_amount", "fee_method"]
                    )
                booked += 1
            self.stdout.write(f"  booked: {booked} places")

        today = timezone.localdate()
        added = 0
        for fields in _standalone_members(association, today):
            joined_on = fields.pop("joined_on")
            _member, created = Member.objects.get_or_create(
                association=association,
                contact_email=fields.pop("contact_email"),
                defaults=fields,
            )
            if created:
                Member.objects.filter(pk=_member.pk).update(joined_on=joined_on)
                added += 1
        self.stdout.write(f"members on the register directly: {added} added")

        User = get_user_model()
        for email, ensure_group in TEST_USERS:
            user, created = User.objects.get_or_create(
                email=email, defaults={"is_staff": True}
            )
            if created:
                user.set_password("1234")
                user.save(update_fields=["password"])
                EmailAddress.objects.update_or_create(
                    user=user,
                    email=user.email,
                    defaults={"verified": True, "primary": True},
                )
            user.groups.set([ensure_group()])
        self.stdout.write(f"test users ready: {', '.join(e for e, _ in TEST_USERS)}")

        self.stdout.write(
            self.style.SUCCESS("demo content ready — this is example data")
        )
