"""Where the applicant is in the form, and which form belongs to each step."""

from intake.forms import (
    ApplicantForm,
    ConsentsForm,
    MemberForm,
    PrivacyNoticeForm,
    ReviewForm,
    StatuteForm,
    SubjectTypeForm,
)
from intake.models import SectionKey

SECTION_FORMS = {
    SectionKey.SUBJECT: SubjectTypeForm,
    SectionKey.APPLICANT: ApplicantForm,
    SectionKey.MEMBER: MemberForm,
    SectionKey.STATUTE: StatuteForm,
    SectionKey.PRIVACY: PrivacyNoticeForm,
    SectionKey.CONSENTS: ConsentsForm,
    SectionKey.REVIEW: ReviewForm,
}


def form_for(submission, step, data=None):
    return SECTION_FORMS[step](data=data, instance=submission)


def neighbours(submission, step):
    """The steps either side of this one, or None at the ends.

    A step the organiser switched off still has to render — the signature is
    not theirs to remove — so it counts as sitting just past the configured path.
    """
    path = submission.path()
    if step not in path:
        return (path[-1] if path else None), None
    index = path.index(step)
    previous = path[index - 1] if index else None
    following = path[index + 1] if index + 1 < len(path) else None
    return previous, following


def position(submission, step):
    """One-based position and total, for the progress line."""
    path = submission.path()
    if step not in path:
        return len(path) + 1, len(path) + 1
    return path.index(step) + 1, len(path)


def incomplete_steps(submission):
    """Every step whose own form would still refuse the data on file.

    The review step is excluded: it is signed in the same request that checks
    this, so it has nothing on file yet.
    """
    missing = []
    for step in submission.path():
        if step == SectionKey.REVIEW:
            continue
        form = SECTION_FORMS[step](data=_data_on_file(submission, step), instance=submission)
        if not form.is_valid():
            missing.append(step)
    return missing


def _data_on_file(submission, step):
    """Re-bind a step's form to what the draft already holds."""
    form = SECTION_FORMS[step](instance=submission)
    data = {}
    for name, field in form.fields.items():
        value = form[name].value()
        if isinstance(value, bool):
            value = str(value)
        data[name] = value
    return data
