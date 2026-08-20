import pytest
from django.core import mail
from django.urls import reverse

from intake.models import Submission, Subscription

pytestmark = pytest.mark.django_db


def _submit(client, submission):
    return client.post(
        reverse("intake:submit", args=[submission.token]),
        {"place": "Novara", "declaration": "on"},
    )


def test_submitting_sends_a_receipt_to_the_applicant(client, minor_submission):
    _submit(client, minor_submission)

    receipt = next(m for m in mail.outbox if minor_submission.applicant_email in m.to)
    assert "Luca Rossi" in receipt.body
    assert reverse("intake:done", args=[minor_submission.token]) in receipt.body


def test_the_receipt_carries_the_fee_the_applicant_committed_to(
    client, minor_submission
):
    _submit(client, minor_submission)

    receipt = next(m for m in mail.outbox if minor_submission.applicant_email in m.to)
    assert "10" in receipt.body


def test_the_second_parent_is_written_to_with_their_own_link(client, minor_submission):
    _submit(client, minor_submission)

    pending = minor_submission.subscriptions.get(role=Subscription.Role.SECOND_PARENT)
    request = next(
        m for m in mail.outbox if minor_submission.second_parent_email in m.to
    )
    assert reverse("intake:second-parent", args=[pending.token]) in request.body
    assert "Luca Rossi" in request.body


def test_nobody_is_written_to_about_consents_that_were_refused(
    client, minor_submission
):
    minor_submission.consent_images = False
    minor_submission.consent_whatsapp = False
    minor_submission.save()

    _submit(client, minor_submission)

    assert not [m for m in mail.outbox if minor_submission.second_parent_email in m.to]


def test_plain_text_mail_is_not_html_escaped(client, minor_submission):
    """An apostrophe in the association name must stay an apostrophe."""
    _submit(client, minor_submission)

    for message in mail.outbox:
        assert "&#x27;" not in message.body
        assert "&amp;" not in message.body


def test_every_link_in_the_mail_can_be_clicked(client, minor_submission, settings):
    """A relative path is dead in a mail client: it has no host to resolve it."""
    settings.SITE_BASE_URL = "https://soci.example.org"

    _submit(client, minor_submission)

    for message in mail.outbox:
        assert "https://soci.example.org/" in message.body


def test_the_resume_link_is_absolute_too(client, public_form, settings):
    settings.SITE_BASE_URL = "https://soci.example.org"
    submission = Submission.objects.create(form=public_form)

    client.post(
        reverse("intake:save", args=[submission.token]),
        {"email": "maria.rossi@example.com"},
    )

    assert "https://soci.example.org/" in mail.outbox[-1].body
