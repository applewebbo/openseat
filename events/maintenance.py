"""Scheduled housekeeping for bookings nobody confirmed."""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from events.models import Booking


def stale_bookings():
    """Unconfirmed bookings for events long over: nobody is coming back to them."""
    cutoff = timezone.now() - timedelta(days=settings.EVENTS_BOOKING_SWEEP_DAYS)
    return Booking.objects.unconfirmed().filter(event__starts_at__lt=cutoff)


def purge_stale_bookings():
    """Delete the booking and, with it, the application that made it.

    A confirmed booking is never touched here: it is already on the register,
    kept for as long as membership records are kept.
    """
    purged = 0
    for booking in stale_bookings().select_related("submission"):
        submission = booking.submission
        booking.delete()
        if submission:
            submission.delete()
        purged += 1
    return purged
