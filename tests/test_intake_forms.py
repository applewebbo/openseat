import pytest

from intake.forms import ConsentsForm, ReviewForm, StatuteForm, SubjectTypeForm
from intake.models import SubjectType
from intake.validators import tax_code_check_character


def test_the_check_character_completes_a_known_tax_code():
    assert tax_code_check_character("MRTMTT25D09F205") == "Z"


@pytest.mark.django_db
def test_a_tax_code_with_a_typo_is_refused(submission, english):
    form = _applicant_form(submission, applicant_tax_code="RSSMRA85D52F952X")

    assert not form.is_valid()
    assert "tax code" in str(form.errors["applicant_tax_code"]).lower()


@pytest.mark.django_db
def test_a_lowercase_tax_code_is_accepted_and_normalised(submission):
    form = _applicant_form(submission, applicant_tax_code="rssmra85d52f952f")

    assert form.is_valid(), form.errors
    assert form.cleaned_data["applicant_tax_code"] == "RSSMRA85D52F952F"


@pytest.mark.django_db
def test_a_postcode_that_is_not_five_digits_is_refused(submission):
    form = _applicant_form(submission, applicant_postcode="281")

    assert not form.is_valid()
    assert "applicant_postcode" in form.errors


@pytest.mark.django_db
def test_the_opening_question_must_be_answered(submission):
    form = SubjectTypeForm(data={}, instance=submission)

    assert not form.is_valid()
    assert "subject_type" in form.errors


@pytest.mark.django_db
def test_applying_for_oneself_never_asks_about_parental_responsibility(submission):
    submission.subject_type = SubjectType.SELF

    form = StatuteForm(instance=submission)

    assert "sole_holder" not in form.fields


@pytest.mark.django_db
def test_applying_for_a_minor_must_declare_parental_responsibility(submission):
    submission.subject_type = SubjectType.MINOR

    form = StatuteForm(data={"accepts_statute": True}, instance=submission)

    assert not form.is_valid()
    assert "sole_holder" in form.errors


@pytest.mark.django_db
def test_declaring_two_holders_requires_naming_the_second(submission):
    submission.subject_type = SubjectType.MINOR

    form = StatuteForm(
        data={"accepts_statute": True, "sole_holder": "False"}, instance=submission
    )

    assert not form.is_valid()
    assert "second_parent_email" in form.errors


@pytest.mark.django_db
def test_a_sole_holder_is_not_asked_for_a_second_parent(submission):
    submission.subject_type = SubjectType.MINOR

    form = StatuteForm(
        data={"accepts_statute": True, "sole_holder": "True"}, instance=submission
    )

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_the_statute_must_be_accepted(submission):
    submission.subject_type = SubjectType.SELF

    form = StatuteForm(data={}, instance=submission)

    assert not form.is_valid()
    assert "accepts_statute" in form.errors


@pytest.mark.django_db
def test_both_image_consents_start_unanswered(submission):
    form = ConsentsForm(instance=submission)

    assert form["consent_images"].value() is None
    assert form["consent_whatsapp"].value() is None


@pytest.mark.django_db
def test_an_unanswered_image_consent_blocks_the_step(submission):
    form = ConsentsForm(data={"consent_images": "True"}, instance=submission)

    assert not form.is_valid()
    assert "consent_whatsapp" in form.errors


@pytest.mark.django_db
def test_refusing_both_image_consents_is_a_valid_answer(submission):
    form = ConsentsForm(
        data={"consent_images": "False", "consent_whatsapp": "False"},
        instance=submission,
    )

    assert form.is_valid(), form.errors
    assert form.save().consent_images is False


@pytest.mark.django_db
def test_the_final_declaration_cannot_be_skipped(minor_submission):
    form = ReviewForm(data={"place": "Novara"}, instance=minor_submission)

    assert not form.is_valid()
    assert "declaration" in form.errors


@pytest.mark.django_db
def test_a_signed_review_carries_place_and_declaration(minor_submission):
    form = ReviewForm(
        data={"place": "Novara", "declaration": True}, instance=minor_submission
    )

    assert form.is_valid(), form.errors


def _applicant_form(submission, **overrides):
    from intake.forms import ApplicantForm

    data = {
        "applicant_first_name": "Maria",
        "applicant_last_name": "Rossi",
        "applicant_birth_date": "12/04/1985",
        "applicant_birth_place": "Novara",
        "applicant_tax_code": "RSSMRA85D52F952F",
        "applicant_street": "Via Roma",
        "applicant_number": "4",
        "applicant_postcode": "28100",
        "applicant_province": "NO",
        "applicant_city": "Novara",
        "applicant_phone": "340 1234567",
        "applicant_email": "maria.rossi@example.com",
    }
    data.update(overrides)
    return ApplicantForm(data=data, instance=submission)


@pytest.mark.django_db
def test_a_tax_code_of_the_wrong_length_is_refused(submission, english):
    form = _applicant_form(submission, applicant_tax_code="RSSMRA85")

    assert not form.is_valid()
    assert "16" in str(form.errors["applicant_tax_code"])


@pytest.mark.django_db
def test_a_comune_from_a_different_province_is_refused(submission):
    """Milano is a real comune, just not one of Novara's."""
    form = _applicant_form(submission, applicant_province="NO", applicant_city="Milano")

    assert not form.is_valid()
    assert "applicant_city" in form.errors


@pytest.mark.django_db
def test_a_missing_province_is_refused(submission):
    form = _applicant_form(submission, applicant_province="")

    assert not form.is_valid()
    assert "applicant_province" in form.errors


@pytest.mark.django_db
def test_reopening_a_draft_keeps_its_comune_selectable(submission):
    """The comune choices are rebuilt from the province already on file, so a
    returning visitor's own city still validates without resubmitting it."""
    submission.applicant_province = "NO"
    submission.applicant_city = "Trecate"
    submission.save()

    form = _applicant_form(submission)

    assert ("Trecate", "Trecate") in form.fields["applicant_city"].choices


@pytest.mark.django_db
def test_the_member_section_scopes_its_own_comune_by_its_own_province(submission):
    from intake.forms import MemberForm

    data = {
        "member_first_name": "Luca",
        "member_last_name": "Rossi",
        "member_birth_date": "03/09/2015",
        "member_birth_place": "Novara",
        "member_tax_code": "RSSLCU15P03F952V",
        "member_street": "Via Roma",
        "member_number": "4",
        "member_province": "NO",
        "member_city": "Novara",
    }

    form = MemberForm(data=data, instance=submission)

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_the_member_form_copies_the_applicants_address_when_the_member_has_none(
    submission,
):
    from intake.forms import MemberForm

    submission.applicant_street = "Via Roma"
    submission.applicant_number = "4"
    submission.applicant_province = "NO"
    submission.applicant_city = "Novara"
    submission.save()

    form = MemberForm(instance=submission)

    assert form["member_street"].value() == "Via Roma"
    assert form["member_number"].value() == "4"
    assert form["member_province"].value() == "NO"
    assert form["member_city"].value() == "Novara"


@pytest.mark.django_db
def test_it_never_overwrites_an_address_the_member_already_has(submission):
    from intake.forms import MemberForm

    submission.applicant_street = "Via Roma"
    submission.applicant_province = "NO"
    submission.applicant_city = "Novara"
    submission.member_street = "Via Torino"
    submission.member_province = "MI"
    submission.member_city = "Milano"
    submission.save()

    form = MemberForm(instance=submission)

    assert form["member_street"].value() == "Via Torino"
    assert form["member_province"].value() == "MI"
    assert form["member_city"].value() == "Milano"


@pytest.mark.django_db
def test_a_bound_resubmission_never_triggers_a_fresh_autofill(submission):
    from intake.forms import MemberForm

    submission.applicant_street = "Via Roma"
    submission.applicant_province = "NO"
    submission.applicant_city = "Novara"
    submission.save()

    data = {
        "member_first_name": "Luca",
        "member_last_name": "Rossi",
        "member_birth_date": "03/09/2015",
        "member_birth_place": "Novara",
        "member_tax_code": "RSSLCU15P03F952V",
        "member_street": "",
        "member_number": "",
        "member_province": "",
        "member_city": "",
    }

    form = MemberForm(data=data, instance=submission)

    assert not form.is_valid()
    assert submission.member_street == ""


@pytest.mark.django_db
def test_autofilled_fields_carry_the_alpine_attrs_for_the_green_border(submission):
    from intake.forms import MemberForm

    submission.applicant_street = "Via Roma"
    submission.applicant_province = "NO"
    submission.applicant_city = "Novara"
    submission.save()

    form = MemberForm(instance=submission)

    assert "x-data" in form.fields["member_street"].widget.attrs
    assert "x-data" not in form.fields["member_first_name"].widget.attrs


@pytest.mark.django_db
def test_the_opening_question_offers_no_blank_fourth_answer(submission):
    """A model field with blank=True would hand the form an empty first choice."""
    form = SubjectTypeForm(instance=submission)

    values = [value for value, _label in form.fields["subject_type"].choices]
    assert values == [SubjectType.SELF, SubjectType.MINOR, SubjectType.PROTECTED]
    assert form["subject_type"].value() in (None, "")


@pytest.mark.django_db
def test_the_statute_checkbox_says_what_is_accepted(submission, english):
    submission.subject_type = SubjectType.SELF

    label = str(StatuteForm(instance=submission).fields["accepts_statute"].label)

    assert "statute" in label.lower()
    assert "fee" in label.lower()


@pytest.mark.django_db
def test_the_final_declaration_states_what_is_declared(minor_submission, english):
    label = str(ReviewForm(instance=minor_submission).fields["declaration"].label)

    assert "true" in label.lower()
    assert "member" in label.lower()


@pytest.mark.django_db
def test_the_second_parent_fields_name_whose_details_they_are(submission, english):
    submission.subject_type = SubjectType.MINOR

    form = StatuteForm(instance=submission)

    assert "their" in str(form.fields["second_parent_first_name"].label).lower()
