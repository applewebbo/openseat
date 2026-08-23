"""Mail around who gets to hold a login on this installation."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_q.tasks import async_task

from core.links import absolute_url
from intake.models import Association

User = get_user_model()


def send_approval_request(user):
    async_task("accounts.notifications.deliver_approval_request", user.pk)


def deliver_approval_request(user_pk):
    user = User.objects.filter(pk=user_pk).first()
    if user is None:
        return
    recipients = list(
        User.objects.filter(is_superuser=True, is_active=True).exclude(email="")
    )
    if not recipients:
        return

    context = {
        "association": Association.current(),
        "pending_user": user,
        "admin_url": absolute_url("admin:accounts_customuser_change", user.pk),
    }
    message = EmailMultiAlternatives(
        subject=_("New sign-up waiting for approval: %(email)s") % {"email": user.email},
        body=render_to_string("account/mail/approval_request.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient.email for recipient in recipients],
    )
    message.attach_alternative(
        render_to_string("account/mail/approval_request.html", context), "text/html"
    )
    message.send()


def send_account_approved(user):
    async_task("accounts.notifications.deliver_account_approved", user.pk)


def deliver_account_approved(user_pk):
    user = User.objects.filter(pk=user_pk).first()
    if user is None:
        return

    context = {
        "association": Association.current(),
        "login_url": absolute_url("account_login"),
    }
    message = EmailMultiAlternatives(
        subject=_("Your account has been approved"),
        body=render_to_string("account/mail/account_approved.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(
        render_to_string("account/mail/account_approved.html", context), "text/html"
    )
    message.send()
