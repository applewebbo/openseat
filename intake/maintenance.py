"""Scheduled housekeeping for drafts nobody came back to."""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from intake.models import Submission
from intake.notifications import deliver_resume_link


def stale_drafts():
    """Drafts old enough to be worth a nudge, with somewhere to send it."""
    cutoff = timezone.now() - timedelta(hours=settings.INTAKE_DRAFT_REMINDER_HOURS)
    return Submission.objects.filter(
        state=Submission.State.DRAFT,
        updated_at__lt=cutoff,
        reminder_sent_at__isnull=True,
    ).exclude(applicant_email="")


def remind_stale_drafts():
    """Write once to each stale draft. Never twice, never to a sent request."""
    reminded = 0
    for submission in stale_drafts():
        if submission.is_expired:
            continue
        deliver_resume_link(submission.pk, reminder=True)
        # Stamped with the queryset to keep updated_at where it was: touching it
        # would push the expiry date out every time the reminder ran.
        Submission.objects.filter(pk=submission.pk).update(
            reminder_sent_at=timezone.now()
        )
        reminded += 1
    return reminded


def purge_expired_drafts():
    """Delete drafts past their expiry: nobody is coming back for them."""
    cutoff = timezone.now() - timedelta(days=settings.INTAKE_DRAFT_EXPIRY_DAYS)
    expired = Submission.objects.filter(
        state=Submission.State.DRAFT, updated_at__lt=cutoff
    )
    return expired.delete()[0]


def run_draft_maintenance():
    """The single entry point the scheduler calls."""
    return {"reminded": remind_stale_drafts(), "purged": purge_expired_drafts()}
