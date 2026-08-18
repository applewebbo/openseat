import pytest
from django.urls import reverse

from intake.models import SectionKey, Submission, Subscription, SubjectType

pytestmark = pytest.mark.django_db


def test_the_public_form_needs_no_account(client, public_form):
    response = client.get(public_form.get_absolute_url())

    assert response.status_code == 200
    assert "Ontano" in response.content.decode()


def test_a_closed_form_says_so_instead_of_starting(client, public_form):
    public_form.is_open = False
    public_form.save()

    response = client.get(public_form.get_absolute_url())

    assert response.status_code == 200
    assert reverse("intake:begin", args=[public_form.slug]) not in response.content.decode()


def test_reading_the_landing_page_creates_no_draft(client, public_form):
    client.get(public_form.get_absolute_url())

    assert not Submission.objects.exists()


def test_starting_creates_a_draft_and_opens_the_first_step(client, public_form):
    response = client.post(reverse("intake:begin", args=[public_form.slug]))

    submission = Submission.objects.get()
    assert submission.state == Submission.State.DRAFT
    assert response.status_code == 302
    assert response.url == _step_url(submission, SectionKey.SUBJECT)


def test_a_closed_form_cannot_be_started(client, public_form):
    public_form.is_open = False
    public_form.save()

    response = client.post(reverse("intake:begin", args=[public_form.slug]))

    assert response.status_code == 404
    assert not Submission.objects.exists()


def test_answering_the_opening_question_moves_to_the_next_step(client, submission):
    response = client.post(
        _step_url(submission, SectionKey.SUBJECT), {"subject_type": SubjectType.MINOR}
    )

    submission.refresh_from_db()
    assert submission.subject_type == SubjectType.MINOR
    assert response.url == _step_url(submission, SectionKey.APPLICANT)


def test_an_invalid_step_redisplays_itself_with_the_error(client, submission):
    response = client.post(_step_url(submission, SectionKey.SUBJECT), {})

    assert response.status_code == 200
    assert response.context["form"].errors


def test_applying_for_oneself_skips_the_member_step(client, submission):
    client.post(
        _step_url(submission, SectionKey.SUBJECT), {"subject_type": SubjectType.SELF}
    )
    submission.refresh_from_db()

    assert SectionKey.MEMBER not in submission.path()


def test_a_step_outside_the_path_is_not_reachable(client, submission):
    submission.subject_type = SubjectType.SELF
    submission.save()

    response = client.get(_step_url(submission, SectionKey.MEMBER))

    assert response.status_code == 302


def test_a_disabled_section_is_not_reachable(client, submission):
    submission.form.sections.filter(key=SectionKey.CONSENTS).update(is_enabled=False)
    submission.subject_type = SubjectType.SELF
    submission.save()

    response = client.get(_step_url(submission, SectionKey.CONSENTS))

    assert response.status_code == 302


def test_an_unknown_token_is_not_found(client, public_form):
    response = client.get(
        reverse(
            "intake:step",
            args=["3f1d2e4a-0000-4000-8000-000000000000", SectionKey.SUBJECT],
        )
    )

    assert response.status_code == 404


def test_a_draft_is_resumed_from_its_own_link(client, minor_submission):
    response = client.get(_step_url(minor_submission, SectionKey.APPLICANT))

    assert response.status_code == 200
    assert b"Maria" in response.content


def test_an_incomplete_request_cannot_be_submitted(client, submission):
    response = client.post(_submit_url(submission))

    submission.refresh_from_db()
    assert submission.state == Submission.State.DRAFT
    assert response.status_code == 302


def test_submitting_signs_the_membership_application(client, minor_submission):
    response = client.post(
        _submit_url(minor_submission), {"place": "Novara", "declaration": "on"}
    )

    minor_submission.refresh_from_db()
    assert minor_submission.state == Submission.State.SUBMITTED
    assert minor_submission.submitted_at is not None
    assert minor_submission.ip
    assert response.url == _done_url(minor_submission)

    signature = minor_submission.subscriptions.get(
        role=Subscription.Role.PRIMARY, subject=Subscription.Subject.MEMBERSHIP
    )
    assert signature.state == Subscription.State.SIGNED
    assert signature.signed_at is not None
    assert signature.declaration


def test_two_holders_leave_the_image_consent_pending(client, minor_submission):
    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})

    pending = minor_submission.subscriptions.get(
        role=Subscription.Role.SECOND_PARENT,
        subject=Subscription.Subject.IMAGE_CONSENT,
    )
    assert pending.state == Subscription.State.PENDING
    assert minor_submission.image_consent_active is False


def test_a_sole_holder_leaves_nothing_pending(client, minor_submission):
    minor_submission.sole_holder = True
    minor_submission.second_parent_email = ""
    minor_submission.save()

    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})

    assert not minor_submission.subscriptions.filter(
        role=Subscription.Role.SECOND_PARENT
    ).exists()
    assert minor_submission.image_consent_active is True


def test_refusing_every_image_consent_asks_nothing_of_the_second_parent(
    client, minor_submission
):
    minor_submission.consent_images = False
    minor_submission.consent_whatsapp = False
    minor_submission.save()

    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})

    assert not minor_submission.subscriptions.filter(
        subject=Subscription.Subject.IMAGE_CONSENT
    ).exists()


def test_a_submitted_request_no_longer_accepts_edits(client, minor_submission):
    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})

    response = client.get(_step_url(minor_submission, SectionKey.APPLICANT))

    assert response.status_code == 302
    assert response.url == _done_url(minor_submission)


def test_the_done_page_reports_a_pending_second_signature(client, minor_submission):
    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})

    response = client.get(_done_url(minor_submission))

    assert response.status_code == 200
    assert b"Paolo" in response.content


def test_the_second_parent_signs_from_their_own_link(client, minor_submission):
    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})
    pending = minor_submission.subscriptions.get(
        role=Subscription.Role.SECOND_PARENT
    )

    response = client.post(
        reverse("intake:second-parent", args=[pending.token]), {"answer": "sign"}
    )

    pending.refresh_from_db()
    assert pending.state == Subscription.State.SIGNED
    assert pending.signed_at is not None
    assert pending.ip
    assert response.status_code == 302
    assert minor_submission.image_consent_active is True


def test_the_second_parent_can_refuse(client, minor_submission):
    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})
    pending = minor_submission.subscriptions.get(role=Subscription.Role.SECOND_PARENT)

    client.post(reverse("intake:second-parent", args=[pending.token]), {"answer": "no"})

    pending.refresh_from_db()
    assert pending.state == Subscription.State.DECLINED
    assert minor_submission.image_consent_active is False


def test_the_second_parent_link_reads_before_it_signs(client, minor_submission):
    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})
    pending = minor_submission.subscriptions.get(role=Subscription.Role.SECOND_PARENT)

    response = client.get(reverse("intake:second-parent", args=[pending.token]))

    assert response.status_code == 200
    assert b"Luca" in response.content


def test_an_already_answered_link_cannot_be_answered_twice(client, minor_submission):
    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})
    pending = minor_submission.subscriptions.get(role=Subscription.Role.SECOND_PARENT)
    url = reverse("intake:second-parent", args=[pending.token])
    client.post(url, {"answer": "sign"})

    response = client.post(url, {"answer": "no"})

    pending.refresh_from_db()
    assert pending.state == Subscription.State.SIGNED
    assert response.status_code == 200


def test_the_client_ip_prefers_the_forwarded_header(client, minor_submission):
    client.post(
        _submit_url(minor_submission),
        {"place": "Novara", "declaration": "on"},
        HTTP_X_FORWARDED_FOR="203.0.113.7, 10.0.0.1",
    )

    minor_submission.refresh_from_db()
    assert minor_submission.ip == "203.0.113.7"


def _step_url(submission, step):
    return reverse("intake:step", args=[submission.token, step])


def _submit_url(submission):
    return reverse("intake:submit", args=[submission.token])


def _done_url(submission):
    return reverse("intake:done", args=[submission.token])


def test_the_review_page_reads_the_answers_back(client, minor_submission):
    response = client.get(reverse("intake:review", args=[minor_submission.token]))

    assert response.status_code == 200
    assert b"RSSLCU15P03F952V" in response.content


def test_a_submitted_request_cannot_be_reviewed_again(client, minor_submission):
    client.post(_submit_url(minor_submission), {"place": "Novara", "declaration": "on"})

    response = client.get(reverse("intake:review", args=[minor_submission.token]))

    assert response.url == _done_url(minor_submission)


def test_the_last_section_leads_to_the_signature(client, minor_submission):
    response = client.post(
        _step_url(minor_submission, SectionKey.CONSENTS),
        {"consent_images": "True", "consent_whatsapp": "False"},
    )

    assert response.url == reverse("intake:review", args=[minor_submission.token])


def test_switching_the_review_section_off_does_not_lose_the_signature(
    client, minor_submission
):
    minor_submission.form.sections.filter(key=SectionKey.REVIEW).update(
        is_enabled=False
    )

    response = client.post(
        _step_url(minor_submission, SectionKey.CONSENTS),
        {"consent_images": "True", "consent_whatsapp": "False"},
    )

    assert response.url == reverse("intake:review", args=[minor_submission.token])
    assert client.get(response.url).status_code == 200


def test_a_signature_without_the_declaration_is_refused(client, minor_submission):
    response = client.post(_submit_url(minor_submission), {"place": "Novara"})

    minor_submission.refresh_from_db()
    assert response.status_code == 200
    assert minor_submission.state == Submission.State.DRAFT
    assert "declaration" in response.context["form"].errors


def test_signing_for_oneself_records_no_parental_declaration(client, submission):
    submission.subject_type = SubjectType.SELF
    submission.applicant_first_name = "Anna"
    submission.applicant_last_name = "Verdi"
    submission.applicant_birth_date = "1970-01-05"
    submission.applicant_birth_place = "Novara"
    submission.applicant_tax_code = "VRDNNA70A45F952I"
    submission.applicant_street = "Via Roma"
    submission.applicant_number = "1"
    submission.applicant_postcode = "28100"
    submission.applicant_city = "Novara"
    submission.applicant_phone = "3401234567"
    submission.applicant_email = "anna.verdi@example.com"
    submission.accepts_statute = True
    submission.consent_images = False
    submission.consent_whatsapp = False
    submission.save()

    client.post(_submit_url(submission), {"place": "Novara", "declaration": "on"})

    submission.refresh_from_db()
    assert submission.state == Submission.State.SUBMITTED
    declaration = submission.subscriptions.get().declaration
    assert "316" not in declaration


@pytest.mark.parametrize(
    "step",
    [
        SectionKey.APPLICANT,
        SectionKey.MEMBER,
        SectionKey.STATUTE,
        SectionKey.PRIVACY,
        SectionKey.CONSENTS,
    ],
)
def test_no_step_leaks_template_syntax_onto_the_page(client, minor_submission, step):
    """A multi-line {# #} is not a comment to Django: it renders."""
    page = client.get(_step_url(minor_submission, step)).content.decode()

    assert "{#" not in page
    assert "{%" not in page
    assert "endcomment" not in page
