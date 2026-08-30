"""What the family gets after booking. Queued like the rest of the mail."""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_q.tasks import async_task

from core.links import absolute_url
from core.mail import from_header
from events.access import contact_token_for, token_for
from events.models import Booking, Event
from intake.models import Association, Submission


def send_booking_confirmation(event, email, submission=None):
    async_task(
        "events.notifications.deliver_booking_confirmation",
        event.pk,
        email,
        submission_pk=submission.pk if submission else None,
    )


def deliver_booking_confirmation(event_pk, email, submission_pk=None):
    event = Event.objects.select_related("association").get(pk=event_pk)
    bookings = event.bookings.active().for_contact(email)
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
        from_email=from_header(event.association),
        to=[email],
        reply_to=[event.association.email],
    )
    message.attach_alternative(
        render_to_string("events/mail/booking.html", context), "text/html"
    )
    message.send()


def send_booking_links(email):
    async_task("events.notifications.deliver_booking_links", email)


def deliver_booking_links(email):
    """The way back in, for somebody who no longer has the confirmation mail."""
    bookings = (
        Booking.objects.active().for_contact(email).upcoming().select_related("event")
    )
    if not bookings:
        return

    association = Association.current()
    context = {
        "association": association,
        "bookings": bookings,
        "manage_url": absolute_url("events:mine", contact_token_for(email)),
        "days": settings.EVENTS_BOOKING_LINK_DAYS,
    }
    message = EmailMultiAlternatives(
        subject=_("Your bookings"),
        body=render_to_string("events/mail/bookings.txt", context),
        from_email=from_header(association),
        to=[email],
        reply_to=[association.email],
    )
    message.attach_alternative(
        render_to_string("events/mail/bookings.html", context), "text/html"
    )
    message.send()
