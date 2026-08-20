"""What the family gets after booking. Queued like the rest of the mail."""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_q.tasks import async_task

from core.links import absolute_url
from events.access import token_for
from events.models import Event
from intake.models import Submission


def send_booking_confirmation(event, email, submission=None):
    async_task(
        "events.notifications.deliver_booking_confirmation",
        event.pk,
        email,
        submission_pk=submission.pk if submission else None,
    )


def deliver_booking_confirmation(event_pk, email, submission_pk=None):
    event = Event.objects.select_related("association").get(pk=event_pk)
    bookings = (
        event.bookings.confirmed()
        .filter(member__contact_email__iexact=email)
        .select_related("member")
    )
    if not bookings:
        return

    submission = (
        Submission.objects.filter(pk=submission_pk).first() if submission_pk else None
    )
    context = {
        "event": event,
        "association": event.association,
        "bookings": bookings,
        "submission": submission,
        "done_url": absolute_url("intake:done", submission.token)
        if submission
        else None,
        "manage_url": absolute_url(
            "events:manage", event.slug, token_for(event, email)
        ),
    }
    message = EmailMultiAlternatives(
        subject=_("Booked: %(event)s") % {"event": event.title},
        body=render_to_string("events/mail/booking.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    message.attach_alternative(
        render_to_string("events/mail/booking.html", context), "text/html"
    )
    message.send()
