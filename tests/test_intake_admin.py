import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from intake.models import Submission

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
