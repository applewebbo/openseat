"""Outbound mail. Queued through django-q2 so a slow SMTP never blocks a reply."""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_q.tasks import async_task

from core.links import absolute_url
from core.mail import attach_logo, from_header
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
    context = {
        "submission": submission,
        "association": association,
        "reminder": reminder,
        "expires_at": submission.expires_at,
        "resume_url": absolute_url(
            "intake:step", submission.token, resume_step(submission)
        ),
    }
    message = EmailMultiAlternatives(
        subject=(
            _("Your application to %(association)s is still open")
            if reminder
            else _("Carry on with your application to %(association)s")
        )
        % {"association": association.name},
        body=render_to_string("intake/mail/resume.txt", context),
        from_email=from_header(association),
        to=[email or submission.applicant_email],
        reply_to=[association.email],
    )
    message.attach_alternative(
        render_to_string("intake/mail/resume.html", context), "text/html"
    )
    attach_logo(message, association)
    message.send()


def deliver_receipt(submission_pk):
    submission = Submission.objects.select_related("form__association").get(
        pk=submission_pk
    )
    association = submission.form.association
    context = {
        "submission": submission,
        "association": association,
        "done_url": absolute_url("intake:done", submission.token),
    }
    message = EmailMultiAlternatives(
        subject=_("Your membership application to %(association)s")
        % {"association": association.name},
        body=render_to_string("intake/mail/receipt.txt", context),
        from_email=from_header(association),
        to=[submission.applicant_email],
        reply_to=[association.email],
    )
    message.attach_alternative(
        render_to_string("intake/mail/receipt.html", context), "text/html"
    )
    attach_logo(message, association)
    message.send()


def deliver_second_parent_request(subscription_pk):
    subscription = Subscription.objects.select_related(
        "submission__form__association"
    ).get(pk=subscription_pk)
    submission = subscription.submission
    association = submission.form.association
    context = {
        "subscription": subscription,
        "submission": submission,
        "association": association,
        "consent_url": absolute_url("intake:second-parent", subscription.token),
    }
    message = EmailMultiAlternatives(
        subject=_("Image consent for %(member)s")
        % {"member": submission.member_display},
        body=render_to_string("intake/mail/second-parent.txt", context),
        from_email=from_header(association),
        to=[subscription.signatory_email],
        reply_to=[association.email],
    )
    message.attach_alternative(
        render_to_string("intake/mail/second-parent.html", context), "text/html"
    )
    attach_logo(message, association)
    message.send()
