import pytest
import tablib

from members.models import Member
from members.resources import MemberResource

pytestmark = pytest.mark.django_db


def _dataset(headers, rows):
    dataset = tablib.Dataset(headers=headers)
    for row in rows:
        dataset.append(row)
    return dataset


HEADERS = [
    "TIPO_ANAGRAFICA",
    "COGNOME",
    "NOME",
    "SETTORE_ISTITUZIONALE_ENTE",
    "DENOMINAZIONE",
    "CODICE_FISCALE",
    "SIGLA_NAZIONE_CODICE_FISCALE",
    "PARTITA_IVA",
    "SIGLA_NAZIONE_PARTITA_IVA",
    "INDIRIZZO",
    "CIVICO",
    "CAP",
    "COMUNE",
    "SIGLA_PROVINCIA",
    "SIGLA_NAZIONE",
    "TELEFONO",
    "CELLULARE",
    "EMAIL",
    "PEC",
    "SITO_WEB",
    "NOTE",
    "TAG",
]


def test_the_export_follows_the_external_tracciato(member_factory, association):
    member_factory(
        association=association,
        first_name="Luca",
        last_name="Rossi",
        tax_code="RSSLCU15P03F952V",
        street="Via Roma",
        number="4",
        postcode="28100",
        city="Novara",
        province="NO",
        contact_phone="3331234567",
        email="luca.rossi@example.com",
    )

    dataset = MemberResource().export()

    assert dataset.headers == HEADERS
    row = dict(zip(dataset.headers, dataset[0], strict=True))
    assert row["COGNOME"] == "Rossi"
    assert row["NOME"] == "Luca"
    assert row["CODICE_FISCALE"] == "RSSLCU15P03F952V"
    assert row["INDIRIZZO"] == "Via Roma"
    assert row["CIVICO"] == "4"
    assert row["CAP"] == "28100"
    assert row["COMUNE"] == "Novara"
    assert row["SIGLA_PROVINCIA"] == "NO"
    assert row["CELLULARE"] == "3331234567"
    assert row["EMAIL"] == "luca.rossi@example.com"
    assert row["SIGLA_NAZIONE"] == "IT"
    assert row["SIGLA_NAZIONE_CODICE_FISCALE"] == "IT"


def test_columns_with_no_home_on_the_register_are_always_blank(
    member_factory, association
):
    member_factory(association=association)

    dataset = MemberResource().export()
    row = dict(zip(dataset.headers, dataset[0], strict=True))

    for column in (
        "TIPO_ANAGRAFICA",
        "SETTORE_ISTITUZIONALE_ENTE",
        "DENOMINAZIONE",
        "PARTITA_IVA",
        "SIGLA_NAZIONE_PARTITA_IVA",
        "TELEFONO",
        "PEC",
        "SITO_WEB",
        "TAG",
    ):
        assert row[column] == ""


def test_note_carries_the_event_the_member_joined_through(
    member_factory, submission, booking_factory, event_factory
):
    event = event_factory(title="Una giornata con gli asini")
    booking_factory(event=event, submission=submission)
    member = member_factory(association=submission.form.association, submission=submission)

    dataset = MemberResource().export(Member.objects.filter(pk=member.pk))
    row = dict(zip(dataset.headers, dataset[0], strict=True))

    expected = f"Una giornata con gli asini - {event.starts_at.strftime('%d/%m/%Y')}"
    assert row["NOTE"] == expected


def test_note_is_blank_for_a_hand_entered_member(member_factory, association):
    member_factory(association=association)

    dataset = MemberResource().export()
    row = dict(zip(dataset.headers, dataset[0], strict=True))

    assert row["NOTE"] == ""


def test_import_overwrite_updates_the_matching_tax_code(member_factory, association):
    member_factory(association=association, tax_code="RSSLCU15P03F952V", city="Novara")
    row = ["" for _ in HEADERS]
    row[HEADERS.index("CODICE_FISCALE")] = "RSSLCU15P03F952V"
    row[HEADERS.index("COGNOME")] = "Rossi"
    row[HEADERS.index("NOME")] = "Luca"
    row[HEADERS.index("COMUNE")] = "Trecate"
    row[HEADERS.index("EMAIL")] = "luca@example.com"
    dataset = _dataset(HEADERS, [row])

    MemberResource(mode="overwrite").import_data(dataset)

    assert Member.objects.filter(association=association).count() == 1
    assert Member.objects.get().city == "Trecate"


def test_import_append_always_creates_a_new_row(member_factory, association):
    member_factory(association=association, tax_code="RSSLCU15P03F952V")
    row = ["" for _ in HEADERS]
    row[HEADERS.index("CODICE_FISCALE")] = "RSSLCU15P03F952V"
    row[HEADERS.index("COGNOME")] = "Rossi"
    row[HEADERS.index("NOME")] = "Luca"
    row[HEADERS.index("EMAIL")] = "luca@example.com"
    dataset = _dataset(HEADERS, [row])

    MemberResource(mode="append").import_data(dataset)

    assert Member.objects.filter(association=association).count() == 2


def test_import_with_a_blank_tax_code_is_always_a_new_row(
    member_factory, association
):
    member_factory(association=association, tax_code="")
    row = ["" for _ in HEADERS]
    row[HEADERS.index("COGNOME")] = "Verdi"
    row[HEADERS.index("NOME")] = "Anna"
    row[HEADERS.index("EMAIL")] = "anna@example.com"
    dataset = _dataset(HEADERS, [row])

    MemberResource(mode="overwrite").import_data(dataset)

    assert Member.objects.filter(association=association).count() == 2


def test_import_backfills_contact_email_from_email_when_blank(association):
    row = ["" for _ in HEADERS]
    row[HEADERS.index("COGNOME")] = "Verdi"
    row[HEADERS.index("NOME")] = "Anna"
    row[HEADERS.index("EMAIL")] = "anna@example.com"
    dataset = _dataset(HEADERS, [row])

    MemberResource(mode="append").import_data(dataset)

    member = Member.objects.get()
    assert member.contact_email == "anna@example.com"
    assert member.contact_name == "Anna Verdi"


def test_import_only_matches_within_the_current_association(
    member_factory, association, association_factory
):
    other = association_factory()
    member_factory(association=other, tax_code="RSSLCU15P03F952V", city="Milano")
    row = ["" for _ in HEADERS]
    row[HEADERS.index("CODICE_FISCALE")] = "RSSLCU15P03F952V"
    row[HEADERS.index("COGNOME")] = "Rossi"
    row[HEADERS.index("NOME")] = "Luca"
    row[HEADERS.index("EMAIL")] = "luca@example.com"
    dataset = _dataset(HEADERS, [row])

    MemberResource(mode="overwrite").import_data(dataset)

    assert Member.objects.get(association=other).city == "Milano"
    assert Member.objects.filter(association=association).count() == 1
