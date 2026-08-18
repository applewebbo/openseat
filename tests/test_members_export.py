import csv
import io
from datetime import date, timedelta

import pytest
import time_machine
from django.core.management import call_command
from django.urls import reverse

from members.export import member_rows, write_csv
from members.models import Member

pytestmark = pytest.mark.django_db


def _joined(member_factory, association, when, **kwargs):
    with time_machine.travel(when, tick=False):
        member = member_factory(association=association, **kwargs)
    Member.objects.filter(pk=member.pk).update(joined_on=when)
    member.refresh_from_db()
    return member


def test_the_export_names_its_columns(member_factory, association):
    member_factory(association=association)

    rows = list(member_rows(Member.objects.all()))

    assert rows[0][:3] == ["Cognome", "Nome", "Data di nascita"]


def test_a_member_becomes_one_row(member_factory, association):
    member_factory(
        association=association, first_name="Luca", last_name="Rossi",
        tax_code="RSSLCU15P03F952V",
    )

    rows = list(member_rows(Member.objects.all()))

    assert rows[1][0] == "Rossi"
    assert rows[1][1] == "Luca"
    assert "RSSLCU15P03F952V" in rows[1]


def test_the_export_carries_who_to_contact(member_factory, association):
    member_factory(
        association=association,
        contact_name="Maria Rossi",
        contact_email="maria@example.com",
    )

    rows = list(member_rows(Member.objects.all()))

    assert "Maria Rossi" in rows[1]
    assert "maria@example.com" in rows[1]


def test_an_unratified_member_says_so_rather_than_leaving_a_blank(
    member_factory, association
):
    member_factory(association=association, ratified_on=None)

    rows = list(member_rows(Member.objects.all()))

    assert "Da ratificare" in rows[1]


def test_the_csv_is_written_with_a_header_and_one_line_per_member(
    member_factory, association
):
    member_factory(association=association, first_name="Luca")
    member_factory(association=association, first_name="Sara")

    buffer = io.StringIO()
    write_csv(buffer, Member.objects.all())

    lines = list(csv.reader(io.StringIO(buffer.getvalue())))
    assert len(lines) == 3


# --- the date range --------------------------------------------------------


def test_the_command_exports_only_the_chosen_range(
    member_factory, association, tmp_path
):
    today = date.today()
    _joined(member_factory, association, today - timedelta(days=40), first_name="Vecchia")
    _joined(member_factory, association, today - timedelta(days=2), first_name="Nuova")
    destination = tmp_path / "soci.csv"

    call_command(
        "export_members",
        "--from", (today - timedelta(days=7)).isoformat(),
        "--to", today.isoformat(),
        "--output", str(destination),
    )

    body = destination.read_text()
    assert "Nuova" in body
    assert "Vecchia" not in body


def test_the_command_writes_everyone_when_no_range_is_given(
    member_factory, association, tmp_path
):
    today = date.today()
    _joined(member_factory, association, today - timedelta(days=400), first_name="Vecchia")
    destination = tmp_path / "soci.csv"

    call_command("export_members", "--output", str(destination))

    assert "Vecchia" in destination.read_text()


def test_the_command_says_how_many_it_wrote(member_factory, association, tmp_path, capsys):
    member_factory(association=association)
    destination = tmp_path / "soci.csv"

    call_command("export_members", "--output", str(destination))

    assert "1" in capsys.readouterr().out


# --- from the admin --------------------------------------------------------


def test_the_organiser_can_export_the_members_they_selected(
    staff_client, member_factory, association
):
    member = member_factory(association=association, first_name="Luca")

    response = staff_client.post(
        reverse("admin:members_member_changelist"),
        {"action": "export_selected", "_selected_action": [str(member.pk)]},
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert b"Luca" in response.content


def test_the_exported_file_is_named_for_the_day_it_was_made(
    staff_client, member_factory, association
):
    member = member_factory(association=association)

    response = staff_client.post(
        reverse("admin:members_member_changelist"),
        {"action": "export_selected", "_selected_action": [str(member.pk)]},
    )

    assert date.today().isoformat() in response["Content-Disposition"]


def test_the_register_can_be_filtered_by_when_people_joined(
    staff_client, member_factory, association
):
    member_factory(association=association)

    response = staff_client.get(reverse("admin:members_member_changelist"))

    assert response.status_code == 200
    assert b"joined_on" in response.content


def test_a_member_with_no_address_exports_an_empty_cell_not_a_stray_comma(
    member_factory, association
):
    member_factory(association=association, street="", number="", city="")

    rows = list(member_rows(Member.objects.all()))

    assert rows[1][5] == ""


def test_the_board_can_minute_admissions_from_the_register(
    staff_client, member_factory, association
):
    member = member_factory(association=association, ratified_on=None)

    staff_client.post(
        reverse("admin:members_member_changelist"),
        {"action": "mark_ratified", "_selected_action": [str(member.pk)]},
    )

    member.refresh_from_db()
    assert member.ratified_on == date.today()


def test_minuting_again_leaves_the_original_date(
    staff_client, member_factory, association
):
    earlier = date.today() - timedelta(days=30)
    member = member_factory(association=association, ratified_on=earlier)

    staff_client.post(
        reverse("admin:members_member_changelist"),
        {"action": "mark_ratified", "_selected_action": [str(member.pk)]},
    )

    member.refresh_from_db()
    assert member.ratified_on == earlier


def test_a_full_address_exports_as_one_readable_line(member_factory, association):
    member_factory(
        association=association,
        street="Via Roma",
        number="4",
        postcode="28100",
        city="Novara",
    )

    rows = list(member_rows(Member.objects.all()))

    assert rows[1][5] == "Via Roma 4, 28100 Novara"
