import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from intake.models import CustomField, Section, Submission

pytestmark = pytest.mark.django_db


def test_the_roster_lists_submissions(staff_client, minor_submission):
    response = staff_client.get(reverse("admin:intake_submission_changelist"))

    assert response.status_code == 200
    assert b"Luca Rossi" in response.content


def test_changelist_query_count_is_stable_with_more_submissions(
    staff_client, minor_submission_factory
):
    minor_submission_factory()
    with CaptureQueriesContext(connection) as ctx:
        staff_client.get(reverse("admin:intake_submission_changelist"))
    baseline = len(ctx.captured_queries)

    minor_submission_factory.create_batch(9)
    with CaptureQueriesContext(connection) as ctx:
        staff_client.get(reverse("admin:intake_submission_changelist"))

    assert len(ctx.captured_queries) == baseline


def test_the_roster_reports_whether_images_may_be_published(
    staff_client, minor_submission
):
    """Two holders and no second signature means the answer is no, not "yes"."""
    response = staff_client.get(reverse("admin:intake_submission_changelist"))

    assert response.status_code == 200
    assert Submission.objects.get().image_consent_active is False


def test_the_roster_can_be_filtered_by_form(
    staff_client, minor_submission, minor_submission_factory
):
    minor_submission_factory()

    response = staff_client.get(
        reverse("admin:intake_submission_changelist"),
        {"form": minor_submission.form_id},
    )

    assert response.status_code == 200
    assert list(response.context["cl"].queryset) == [minor_submission]


def test_forms_expose_their_section_switches(staff_client, public_form):
    response = staff_client.get(
        reverse("admin:intake_publicform_change", args=[public_form.pk])
    )

    assert response.status_code == 200
    assert b"is_enabled" in response.content


def test_associations_are_editable(staff_client, association):
    response = staff_client.get(
        reverse("admin:intake_association_change", args=[association.pk])
    )

    assert response.status_code == 200


def test_the_home_page_fields_are_edited_with_the_rich_text_editor(
    staff_client, association
):
    response = staff_client.get(
        reverse("admin:intake_association_change", args=[association.pk])
    )

    assert b"home_title" in response.content
    assert b"django_ckeditor_5" in response.content


def test_the_association_slug_is_neither_editable_nor_shown(staff_client, association):
    response = staff_client.get(
        reverse("admin:intake_association_change", args=[association.pk])
    )

    assert "slug" not in response.context["adminform"].form.fields
    assert b'name="slug"' not in response.content


def test_a_second_association_cannot_be_added(staff_client, association):
    """One installation, one association: the add form is closed once it exists."""
    response = staff_client.get(reverse("admin:intake_association_add"))

    assert response.status_code == 403


def test_the_first_association_can_be_added(staff_client):
    response = staff_client.get(reverse("admin:intake_association_add"))

    assert response.status_code == 200


def test_the_association_cannot_be_deleted(staff_client, association):
    response = staff_client.get(
        reverse("admin:intake_association_delete", args=[association.pk])
    )

    assert response.status_code == 403


def test_the_add_form_offers_no_statute_or_consent_only_fields(
    staff_client, public_form
):
    """Those belong to one specific fixed section each; on a blank add form
    they would just sit there unexplained."""
    response = staff_client.get(reverse("admin:intake_section_add"))

    fields = response.context["adminform"].form.fields
    assert "custom_body" not in fields
    assert "consent_images_label" not in fields
    assert "consent_whatsapp_label" not in fields


def test_the_statute_sections_change_form_offers_its_custom_text(
    staff_client, public_form
):
    section = public_form.sections.get(key="statute")

    response = staff_client.get(
        reverse("admin:intake_section_change", args=[section.pk])
    )

    fields = response.context["adminform"].form.fields
    assert "custom_body" in fields
    assert "consent_images_label" not in fields


def test_the_consents_sections_change_form_offers_its_labels(staff_client, public_form):
    section = public_form.sections.get(key="consents")

    response = staff_client.get(
        reverse("admin:intake_section_change", args=[section.pk])
    )

    fields = response.context["adminform"].form.fields
    assert "consent_images_label" in fields
    assert "consent_whatsapp_label" in fields
    assert "custom_body" not in fields


def test_a_custom_sections_change_form_offers_neither(staff_client, public_form):
    section = public_form.sections.create(key="orario", title="Orario", is_custom=True)

    response = staff_client.get(
        reverse("admin:intake_section_change", args=[section.pk])
    )

    fields = response.context["adminform"].form.fields
    assert "custom_body" not in fields
    assert "consent_images_label" not in fields
    assert "consent_whatsapp_label" not in fields


def test_adding_a_section_from_its_own_admin_creates_a_custom_one(
    staff_client, public_form
):
    response = staff_client.post(
        reverse("admin:intake_section_add"),
        {
            "form": public_form.pk,
            "title": "Orario preferito",
            "custom_body": "",
            "consent_images_label": "",
            "consent_whatsapp_label": "",
            "order": 10,
            "is_enabled": "on",
        },
    )

    assert response.status_code == 302
    section = Section.objects.get(title="Orario preferito")
    assert section.is_custom is True
    assert section.key == "orario-preferito"


def test_a_colliding_custom_section_title_gets_a_numeric_suffix(
    staff_client, public_form
):
    public_form.sections.create(key="orario", title="Orario", is_custom=True)

    staff_client.post(
        reverse("admin:intake_section_add"),
        {
            "form": public_form.pk,
            "title": "Orario",
            "custom_body": "",
            "consent_images_label": "",
            "consent_whatsapp_label": "",
            "order": 11,
            "is_enabled": "on",
        },
    )

    assert public_form.sections.filter(key="orario-2").exists()


def test_a_custom_section_without_a_title_is_rejected_with_an_error(
    staff_client, public_form
):
    response = staff_client.post(
        reverse("admin:intake_section_add"),
        {
            "form": public_form.pk,
            "title": "",
            "custom_body": "",
            "consent_images_label": "",
            "consent_whatsapp_label": "",
            "order": 10,
            "is_enabled": "on",
        },
    )

    assert response.status_code == 200
    assert response.context["adminform"].form.errors


def test_the_key_of_a_fixed_section_cannot_be_edited(staff_client, public_form):
    section = public_form.sections.get(key="statute")

    response = staff_client.get(
        reverse("admin:intake_section_change", args=[section.pk])
    )

    assert response.status_code == 200
    assert "key" not in response.context["adminform"].form.fields


def test_a_custom_section_offers_the_custom_field_inline(staff_client, public_form):
    section = public_form.sections.create(key="orario", title="Orario", is_custom=True)

    response = staff_client.get(
        reverse("admin:intake_section_change", args=[section.pk])
    )

    assert b"custom_fields" in response.content


def test_a_fixed_section_offers_no_custom_field_inline(staff_client, public_form):
    section = public_form.sections.get(key="statute")

    response = staff_client.get(
        reverse("admin:intake_section_change", args=[section.pk])
    )

    assert b"custom_fields" not in response.content


def test_a_select_fields_choices_are_editable_in_its_own_admin(
    staff_client, public_form
):
    section = public_form.sections.create(key="orario", title="Orario", is_custom=True)
    custom_field = section.custom_fields.create(
        label="Fascia", field_type=CustomField.FieldType.SELECT
    )

    response = staff_client.get(
        reverse("admin:intake_customfield_change", args=[custom_field.pk])
    )

    assert response.status_code == 200
    assert b"choices" in response.content


def test_a_text_fields_admin_offers_no_choices_inline(staff_client, public_form):
    section = public_form.sections.create(key="orario", title="Orario", is_custom=True)
    custom_field = section.custom_fields.create(
        label="Preferenza", field_type=CustomField.FieldType.TEXT
    )

    response = staff_client.get(
        reverse("admin:intake_customfield_change", args=[custom_field.pk])
    )

    assert b"choices" not in response.content
