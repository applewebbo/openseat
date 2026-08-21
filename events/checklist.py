"""The list whoever is on the door needs before the event starts."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from events.models import Event

logger = logging.getLogger(__name__)


def send_due_checklists():
    """Mail the booking list for every event starting today, once each."""
    sent = 0
    for event in Event.objects.due_for_checklist().select_related("association"):
        send_checklist(event)
        sent += 1
    return sent


def send_checklist(event):
    bookings = event.bookings.active()
    body = render_to_string(
        "events/mail/checklist.txt",
        {"event": event, "association": event.association, "bookings": bookings},
    )
    send_mail(
        subject=_("Bookings for %(event)s") % {"event": event.title},
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[event.association.email],
    )
    # Stamped after sending, so a failure leaves the event due rather than
    # silently marking a list that never arrived.
    Event.objects.filter(pk=event.pk).update(checklist_sent_at=timezone.now())
    logger.info("checklist sent for %s", event)
