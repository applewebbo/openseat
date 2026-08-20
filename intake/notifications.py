"""Outbound mail. Queued through django-q2 so a slow SMTP never blocks a reply."""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_q.tasks import async_task

from core.links import absolute_url
from intake.models import Submission, Subscription
from intake.wizard import resume_step


def send_receipt(submission):
    async_task("intake.notifications.deliver_receipt", submission.pk)


def notify_second_parent(subscription):
    async_task("intake.notifications.deliver_second_parent_request", subscription.pk)


def send_resume_link(submission, email):
    async_task("intake.notifications.deliver_resume_link", submission.pk, email=email)


def deliver_resume_link(submission_pk, email=None, reminder=False):
    """The link back into a draft, either asked for or offered after a silence."""
    submission = Submission.objects.select_related("form__association").get(
        pk=submission_pk
    )
    association = submission.form.association
    body = render_to_string(
        "intake/mail/resume.txt",
        {
            "submission": submission,
            "association": association,
            "reminder": reminder,
            "expires_at": submission.expires_at,
            "resume_url": absolute_url(
                "intake:step", submission.token, resume_step(submission)
            ),
        },
    )
    send_mail(
        subject=(
            _("Your application to %(association)s is still open")
            if reminder
            else _("Carry on with your application to %(association)s")
        )
        % {"association": association.name},
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email or submission.applicant_email],
    )


def deliver_receipt(submission_pk):
    submission = Submission.objects.select_related("form__association").get(
        pk=submission_pk
    )
    association = submission.form.association
    body = render_to_string(
        "intake/mail/receipt.txt",
        {
            "submission": submission,
            "association": association,
            "done_url": absolute_url("intake:done", submission.token),
        },
    )
    send_mail(
        subject=_("Your membership application to %(association)s")
        % {"association": association.name},
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[submission.applicant_email],
    )


def deliver_second_parent_request(subscription_pk):
    subscription = Subscription.objects.select_related(
        "submission__form__association"
    ).get(pk=subscription_pk)
    submission = subscription.submission
    association = submission.form.association
    body = render_to_string(
        "intake/mail/second-parent.txt",
        {
            "subscription": subscription,
            "submission": submission,
            "association": association,
            "consent_url": absolute_url("intake:second-parent", subscription.token),
        },
    )
    send_mail(
        subject=_("Image consent for %(member)s")
        % {"member": submission.member_display},
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[subscription.signatory_email],
    )
