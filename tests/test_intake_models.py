import pytest

from intake.models import Association, SectionKey, SubjectType


@pytest.mark.django_db
def test_association_str_is_its_name(association):
    assert str(association) == association.name


@pytest.mark.django_db
def test_current_is_cached_across_calls(association, django_assert_num_queries):
    Association.current()  # warms the cache

    with django_assert_num_queries(0):
        for _ in range(3):
            Association.current()


@pytest.mark.django_db
def test_current_cache_is_invalidated_on_save(association):
    Association.current()

    association.name = "Nuovo nome"
    association.save()

    assert Association.current().name == "Nuovo nome"


@pytest.mark.django_db
def test_current_returns_none_before_any_association_exists(db):
    assert Association.current() is None


@pytest.mark.django_db
def test_public_form_str_joins_association_and_title(public_form):
    assert str(public_form) == f"{public_form.association.name} — {public_form.title}"


@pytest.mark.django_db
def test_marking_a_form_default_unmarks_the_previous_one(
    association, public_form_factory
):
    first = public_form_factory(association=association, is_default=True)
    second = public_form_factory(association=association, is_default=True)

    first.refresh_from_db()
    assert first.is_default is False
    assert second.is_default is True


@pytest.mark.django_db
def test_a_default_form_of_another_association_is_left_alone(
    association_factory, public_form_factory
):
    one, other = association_factory(), association_factory()
    form_one = public_form_factory(association=one, is_default=True)
    form_other = public_form_factory(association=other, is_default=True)

    form_one.refresh_from_db()
    form_other.refresh_from_db()
    assert form_one.is_default is True
    assert form_other.is_default is True


@pytest.mark.django_db
def test_an_age_bracket_reads_as_its_label(age_bracket):
    age_bracket.label = "18-64"
    assert str(age_bracket) == "18-64"


@pytest.mark.django_db
def test_a_bracket_with_no_bounds_matches_any_age(age_bracket_factory):
    bracket = age_bracket_factory(min_age=None, max_age=None)

    assert bracket.matches(0) is True
    assert bracket.matches(120) is True


@pytest.mark.django_db
def test_a_bracket_matches_within_its_inclusive_bounds(age_bracket_factory):
    bracket = age_bracket_factory(min_age=13, max_age=17)

    assert bracket.matches(13) is True
    assert bracket.matches(17) is True
    assert bracket.matches(12) is False
    assert bracket.matches(18) is False


@pytest.mark.django_db
def test_a_bracket_with_only_a_lower_bound_is_open_ended(age_bracket_factory):
    bracket = age_bracket_factory(min_age=65, max_age=None)

    assert bracket.matches(65) is True
    assert bracket.matches(200) is True
    assert bracket.matches(64) is False


@pytest.mark.django_db
def test_subject_birth_date_is_the_applicants_for_a_self_application(
    adult_submission,
):
    assert adult_submission.subject_birth_date == adult_submission.applicant_birth_date


@pytest.mark.django_db
def test_subject_birth_date_is_the_members_for_someone_else(minor_submission):
    assert minor_submission.subject_birth_date == minor_submission.member_birth_date


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
