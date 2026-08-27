import io

import pytest
from django.urls import reverse

from members.models import Member

pytestmark = pytest.mark.django_db

HEADERS = (
    "TIPO_ANAGRAFICA,COGNOME,NOME,SETTORE_ISTITUZIONALE_ENTE,DENOMINAZIONE,"
    "CODICE_FISCALE,SIGLA_NAZIONE_CODICE_FISCALE,PARTITA_IVA,"
    "SIGLA_NAZIONE_PARTITA_IVA,INDIRIZZO,CIVICO,CAP,COMUNE,SIGLA_PROVINCIA,"
    "SIGLA_NAZIONE,TELEFONO,CELLULARE,EMAIL,PEC,SITO_WEB,NOTE,TAG"
)


def _csv_row(**overrides):
    fields = {name: "" for name in HEADERS.split(",")}
    fields.update(overrides)
    return ",".join(fields[name] for name in HEADERS.split(","))


def test_export_page_loads(staff_client, member, association):
    response = staff_client.get(reverse("admin:members_member_export"))

    assert response.status_code == 200


def test_the_organiser_can_export_the_members_they_selected(
    staff_client, member_factory, association
):
    member = member_factory(association=association, first_name="Luca")

    picker = staff_client.post(
        reverse("admin:members_member_changelist"),
        {"action": "export_admin_action", "_selected_action": [str(member.pk)]},
    )
    assert picker.status_code == 200
    export_form = picker.context["form"]
    field_choices = {name: True for name in export_form.fields if name.startswith("memberresource_")}

    response = staff_client.post(
        reverse("admin:members_member_export"),
        {**export_form.initial, **field_choices, "format": "0", "resource": "0"},
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert b"Luca" in response.content


def test_import_page_loads(staff_client, association):
    response = staff_client.get(reverse("admin:members_member_import"))

    assert response.status_code == 200
    assert b"mode" in response.content


def test_a_full_import_round_trip_creates_a_member(staff_client, association):
    csv_content = HEADERS + "\n" + _csv_row(COGNOME="Verdi", NOME="Anna", EMAIL="anna@example.com")
    upload = io.BytesIO(csv_content.encode("utf-8"))
    upload.name = "soci.csv"

    response = staff_client.post(
        reverse("admin:members_member_import"),
        {
            "import_file": upload,
            "format": "0",
            "resource": "0",
            "mode": "append",
        },
    )
    assert response.status_code == 200
    confirm_form = response.context["confirm_form"]
    assert not response.context["result"].has_errors()

    confirm_response = staff_client.post(
        reverse("admin:members_member_process_import"), confirm_form.initial
    )

    assert confirm_response.status_code == 302
    member = Member.objects.get(association=association)
    assert member.first_name == "Anna"
    assert member.last_name == "Verdi"
