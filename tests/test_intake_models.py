import pytest

from intake.models import SectionKey, SubjectType


@pytest.mark.django_db
def test_association_str_is_its_name(association):
    assert str(association) == association.name


@pytest.mark.django_db
def test_public_form_str_joins_association_and_title(public_form):
    assert str(public_form) == f"{public_form.association.name} — {public_form.title}"


@pytest.mark.django_db
def test_membership_form_ships_the_full_section_catalogue(public_form):
    assert [section.key for section in public_form.sections.all()] == [
        SectionKey.SUBJECT,
        SectionKey.APPLICANT,
        SectionKey.MEMBER,
        SectionKey.STATUTE,
        SectionKey.PRIVACY,
        SectionKey.CONSENTS,
        SectionKey.REVIEW,
    ]


@pytest.mark.django_db
def test_disabled_sections_leave_the_path(public_form):
    public_form.sections.filter(key=SectionKey.CONSENTS).update(is_enabled=False)

    assert SectionKey.CONSENTS not in public_form.path(SubjectType.MINOR)


@pytest.mark.django_db
def test_the_member_section_is_skipped_when_applying_for_oneself(public_form):
    assert SectionKey.MEMBER not in public_form.path(SubjectType.SELF)
    assert SectionKey.MEMBER in public_form.path(SubjectType.MINOR)


@pytest.mark.django_db
def test_an_unanswered_subject_type_still_yields_the_opening_step(public_form):
    assert public_form.path("") == [SectionKey.SUBJECT]


@pytest.mark.django_db
def test_submission_starts_as_a_draft_with_its_own_token(submission):
    assert submission.state == submission.State.DRAFT
    assert submission.token


@pytest.mark.django_db
def test_applying_for_oneself_never_needs_a_second_parent(submission):
    submission.subject_type = SubjectType.SELF

    assert submission.needs_second_parent is False


@pytest.mark.django_db
def test_a_sole_holder_of_parental_responsibility_signs_alone(submission):
    submission.subject_type = SubjectType.MINOR
    submission.sole_holder = True

    assert submission.needs_second_parent is False


@pytest.mark.django_db
def test_two_holders_of_parental_responsibility_need_the_second_signature(submission):
    submission.subject_type = SubjectType.MINOR
    submission.sole_holder = False

    assert submission.needs_second_parent is True


@pytest.mark.django_db
def test_image_diffusion_stays_inactive_until_the_second_parent_confirms(submission):
    submission.subject_type = SubjectType.MINOR
    submission.sole_holder = False
    submission.consent_images = True
    submission.save()

    assert submission.image_consent_active is False


@pytest.mark.django_db
def test_image_diffusion_activates_once_the_second_parent_signs(
    submission, subscription_factory
):
    submission.subject_type = SubjectType.MINOR
    submission.sole_holder = False
    submission.consent_images = True
    submission.save()
    subscription_factory(
        submission=submission,
        role=submission.subscriptions.model.Role.SECOND_PARENT,
        subject=submission.subscriptions.model.Subject.IMAGE_CONSENT,
        state=submission.subscriptions.model.State.SIGNED,
    )

    assert submission.image_consent_active is True


@pytest.mark.django_db
def test_a_sole_holder_activates_image_diffusion_on_their_own(submission):
    submission.subject_type = SubjectType.MINOR
    submission.sole_holder = True
    submission.consent_images = True
    submission.save()

    assert submission.image_consent_active is True


@pytest.mark.django_db
def test_a_refused_image_consent_is_never_active(submission):
    submission.subject_type = SubjectType.SELF
    submission.consent_images = False
    submission.save()

    assert submission.image_consent_active is False


@pytest.mark.django_db
def test_subscription_str_names_signatory_and_subject(subscription):
    assert subscription.signatory_name in str(subscription)
    assert subscription.get_subject_display() in str(subscription)


@pytest.mark.django_db
def test_applying_for_oneself_shows_the_applicant_as_the_member(submission):
    submission.subject_type = SubjectType.SELF
    submission.applicant_first_name = "Anna"
    submission.applicant_last_name = "Verdi"

    assert submission.member_display == "Anna Verdi"
