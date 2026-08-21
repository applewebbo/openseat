from django.contrib.auth.decorators import login_not_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from events.models import Booking
from events.notifications import send_booking_confirmation
from intake.forms import ResumeLinkForm, ReviewForm
from intake.models import PublicForm, SectionKey, Submission, Subscription
from intake.notifications import (
    notify_second_parent,
    send_receipt,
    send_resume_link,
)
from intake.wizard import (
    form_for,
    incomplete_steps,
    neighbours,
    position,
    resume_step,
)
from members.register import enrol

DRAFT_SESSION_KEY = "intake_draft"


def remembered_draft(request, public_form):
    """The draft this browser already opened on this form, if it still stands."""
    token = request.session.get(DRAFT_SESSION_KEY)
    if not token:
        return None
    draft = Submission.objects.filter(
        token=token, form=public_form, state=Submission.State.DRAFT
    ).first()
    if draft is None or draft.is_expired:
        return None
    return draft


def gone(request, submission):
    """A draft past its expiry is not an error to debug: it is simply over."""
    return render(
        request,
        "intake/expired.html",
        {"submission": submission, "association": submission.form.association},
        status=410,
    )


def client_ip(request):
    """The caller's address, reading through a proxy when one is in front."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@login_not_required
def landing(request, slug):
    """What the form is, who it belongs to, and what you need before starting."""
    public_form = get_object_or_404(PublicForm, slug=slug)
    resumable = remembered_draft(request, public_form)
    return render(
        request,
        "intake/landing.html",
        {
            "public_form": public_form,
            "association": public_form.association,
            "resumable": resumable,
            "resumable_step": resume_step(resumable) if resumable else None,
        },
    )


@login_not_required
@require_POST
def begin(request, slug):
    """Open a draft. Deliberately not a GET: reading a page enrols nobody."""
    public_form = get_object_or_404(PublicForm, slug=slug, is_open=True)
    submission = Submission.objects.create(form=public_form)
    # Remembered here so a return visit is offered the draft instead of quietly
    # opening a second one. The emailed link covers other devices.
    request.session[DRAFT_SESSION_KEY] = str(submission.token)
    return redirect("intake:step", token=submission.token, step=SectionKey.SUBJECT)


@login_not_required
def step(request, token, step):
    """Render or advance exactly one section."""
    submission = get_object_or_404(Submission, token=token)
    if submission.state == Submission.State.SUBMITTED:
        return redirect("intake:done", token=submission.token)
    if submission.is_expired:
        return gone(request, submission)
    if step not in submission.path():
        return redirect(
            "intake:step", token=submission.token, step=resume_step(submission)
        )

    if request.method == "POST":
        form = form_for(submission, step, data=request.POST)
        if form.is_valid():
            form.save()
            _, following = neighbours(submission, step)
            if following == SectionKey.REVIEW or following is None:
                # An organiser may switch the review section off; the signature
                # step is not theirs to remove, so the path ends there anyway.
                return redirect("intake:review", token=submission.token)
            return redirect("intake:step", token=submission.token, step=following)
    else:
        form = form_for(submission, step)

    return render(request, "intake/step.html", _step_context(submission, step, form))


@login_not_required
def review(request, token):
    """Read everything back, then sign. Rendering only; signing is submit's job."""
    submission = get_object_or_404(Submission, token=token)
    if submission.state == Submission.State.SUBMITTED:
        return redirect("intake:done", token=submission.token)
    if submission.is_expired:
        return gone(request, submission)
    form = ReviewForm(instance=submission)
    return render(
        request,
        "intake/step.html",
        _step_context(submission, SectionKey.REVIEW, form),
    )


@login_not_required
@require_POST
def submit(request, token):
    """Sign the request: one act, recorded with its time and address."""
    submission = get_object_or_404(
        Submission, token=token, state=Submission.State.DRAFT
    )
    if submission.is_expired:
        return gone(request, submission)
    missing = incomplete_steps(submission)
    if missing:
        return redirect("intake:step", token=token, step=missing[0])

    form = ReviewForm(data=request.POST, instance=submission)
    if not form.is_valid():
        return render(
            request,
            "intake/step.html",
            _step_context(submission, SectionKey.REVIEW, form),
        )

    submission = form.save(commit=False)
    submission.state = Submission.State.SUBMITTED
    submission.submitted_at = timezone.now()
    submission.ip = client_ip(request)
    submission.save()
    _record_signatures(submission, client_ip(request))
    if submission.event_id:
        # Booking is not joining: the register entry waits for the association
        # to confirm attendance and payment, after the event.
        Booking.objects.book_application(submission.event, submission)
        # One act, one mail: the confirmation says everything the receipt says
        # and names the booking too, so sending both would repeat itself.
        send_booking_confirmation(
            submission.event, submission.applicant_email, submission=submission
        )
    else:
        enrol(submission)
        send_receipt(submission)
    return redirect("intake:done", token=token)


@login_not_required
def save(request, token):
    """Hand back the link into this draft, and email it on request."""
    submission = get_object_or_404(Submission, token=token)
    if submission.state == Submission.State.SUBMITTED:
        return redirect("intake:done", token=submission.token)
    if submission.is_expired:
        return gone(request, submission)

    if request.method == "POST":
        form = ResumeLinkForm(data=request.POST)
        if form.is_valid():
            send_resume_link(submission, form.cleaned_data["email"])
            return redirect("intake:saved", token=submission.token)
    else:
        form = ResumeLinkForm(initial={"email": submission.applicant_email})

    return render(
        request,
        "intake/save.html",
        {
            "submission": submission,
            "association": submission.form.association,
            "public_form": submission.form,
            "form": form,
            "resume_step": resume_step(submission),
        },
    )


@login_not_required
def saved(request, token):
    submission = get_object_or_404(Submission, token=token)
    return render(
        request,
        "intake/saved.html",
        {
            "submission": submission,
            "association": submission.form.association,
            "public_form": submission.form,
            "resume_step": resume_step(submission),
        },
    )


@login_not_required
def done(request, token):
    submission = get_object_or_404(Submission, token=token)
    return render(
        request,
        "intake/done.html",
        {
            "submission": submission,
            "association": submission.form.association,
            "pending": submission.subscriptions.filter(
                state=Subscription.State.PENDING
            ).first(),
        },
    )


@login_not_required
def second_parent(request, token):
    """The other holder of parental responsibility answers on image diffusion."""
    subscription = get_object_or_404(
        Subscription, token=token, role=Subscription.Role.SECOND_PARENT
    )
    if request.method == "POST" and subscription.state == Subscription.State.PENDING:
        signed = request.POST.get("answer") == "sign"
        subscription.state = (
            Subscription.State.SIGNED if signed else Subscription.State.DECLINED
        )
        subscription.signed_at = timezone.now()
        subscription.ip = client_ip(request)
        subscription.save()
        return redirect("intake:second-parent", token=token)

    submission = subscription.submission
    return render(
        request,
        "intake/second-parent.html",
        {
            "subscription": subscription,
            "submission": submission,
            "association": submission.form.association,
        },
    )


def _step_context(submission, step, form):
    previous, _following = neighbours(submission, step)
    current, total = position(submission, step)
    return {
        "submission": submission,
        "association": submission.form.association,
        "public_form": submission.form,
        "form": form,
        "step": step,
        "step_label": SectionKey(step).label,
        "previous_step": previous,
        "current_position": current,
        "total_positions": total,
        "progress": round(current / total * 100),
        # Before the opening question is answered the rest of the path is
        # unknown, so a counter here would claim a length nobody chose yet.
        "path_known": bool(submission.subject_type),
    }


def _record_signatures(submission, ip):
    """One row per signature, plus the pending one when a second holder exists."""
    Subscription.objects.create(
        submission=submission,
        signatory_name=f"{submission.applicant_first_name} {submission.applicant_last_name}".strip(),
        signatory_email=submission.applicant_email,
        role=Subscription.Role.PRIMARY,
        subject=Subscription.Subject.MEMBERSHIP,
        state=Subscription.State.SIGNED,
        declaration=_membership_declaration(submission),
        signed_at=submission.submitted_at,
        ip=ip,
    )

    wants_images = bool(submission.consent_images or submission.consent_whatsapp)
    if wants_images and submission.needs_second_parent:
        pending = Subscription.objects.create(
            submission=submission,
            signatory_name=f"{submission.second_parent_first_name} {submission.second_parent_last_name}".strip(),
            signatory_email=submission.second_parent_email,
            role=Subscription.Role.SECOND_PARENT,
            subject=Subscription.Subject.IMAGE_CONSENT,
            state=Subscription.State.PENDING,
        )
        notify_second_parent(pending)


def _membership_declaration(submission):
    """The words the applicant actually subscribed to, kept with the signature."""
    lines = [
        _(
            "Application for membership of %(association)s, accepting its statute and "
            "undertaking to pay the annual fee."
        )
        % {"association": submission.form.association.name}
    ]
    if submission.applies_for_someone_else:
        if submission.sole_holder:
            lines.append(_("Signed as sole holder of parental responsibility."))
        else:
            lines.append(
                _(
                    "Signed on behalf of the other parent too, in agreement with "
                    "them, under artt. 316 and 337-ter of the Civil Code."
                )
            )
    return "\n".join(str(line) for line in lines)
