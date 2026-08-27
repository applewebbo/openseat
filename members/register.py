"""Turning a signed application into a register entry."""

from intake.models import SubjectType
from members.models import Member


def enrol(submission):
    """Put the person the application is for on the register.

    Runs on submission rather than on board approval: that is how it works in
    practice, and gating on a meeting would stop anyone joining the evening
    before an event. `ratified_on` records the minute when it comes.
    """
    if hasattr(submission, "member"):
        return submission.member

    for_someone_else = submission.subject_type != SubjectType.SELF
    if for_someone_else:
        person = {
            "first_name": submission.member_first_name,
            "last_name": submission.member_last_name,
            "birth_date": submission.member_birth_date,
            "birth_place": submission.member_birth_place,
            "tax_code": submission.member_tax_code,
            "street": submission.member_street,
            "number": submission.member_number,
            # The form never asks for the child's postcode — the paper one does
            # not either — and a child living at another address than the parent
            # who enrols them is not a case this association has.
            "postcode": submission.applicant_postcode,
            "city": submission.member_city,
            "province": submission.member_province,
            "email": "",
        }
    else:
        person = {
            "first_name": submission.applicant_first_name,
            "last_name": submission.applicant_last_name,
            "birth_date": submission.applicant_birth_date,
            "birth_place": submission.applicant_birth_place,
            "tax_code": submission.applicant_tax_code,
            "street": submission.applicant_street,
            "number": submission.applicant_number,
            "postcode": submission.applicant_postcode,
            "city": submission.applicant_city,
            "province": submission.applicant_province,
            "email": submission.applicant_email,
        }

    return Member.objects.create(
        association=submission.form.association,
        submission=submission,
        contact_name=f"{submission.applicant_first_name} {submission.applicant_last_name}".strip(),
        contact_email=submission.applicant_email,
        contact_phone=submission.applicant_phone,
        **person,
    )
