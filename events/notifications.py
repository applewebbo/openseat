"""What the family gets after booking. Queued like the rest of the mail."""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_q.tasks import async_task

from core.links import absolute_url
from events.access import token_for
from events.models import Event


def send_booking_confirmation(event, email):
    async_task("events.notifications.deliver_booking_confirmation", event.pk, email)


def deliver_booking_confirmation(event_pk, email):
    event = Event.objects.select_related("association").get(pk=event_pk)
    bookings = (
        event.bookings.confirmed()
        .filter(member__contact_email__iexact=email)
        .select_related("member")
    )
    if not bookings:
        return

    context = {
        "event": event,
        "association": event.association,
        "bookings": bookings,
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
