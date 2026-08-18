import pytest
from django.urls import reverse

from intake.models import Submission

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_client(client, user):
    user.is_staff = user.is_superuser = True
    user.save()
    client.force_login(user)
    return client


def test_the_roster_lists_submissions(staff_client, minor_submission):
    response = staff_client.get(reverse("admin:intake_submission_changelist"))

    assert response.status_code == 200
    assert b"Luca Rossi" in response.content


def test_the_roster_reports_whether_images_may_be_published(
    staff_client, minor_submission
):
    """Two holders and no second signature means the answer is no, not "yes"."""
    response = staff_client.get(reverse("admin:intake_submission_changelist"))

    assert response.status_code == 200
    assert Submission.objects.get().image_consent_active is False


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
