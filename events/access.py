"""The link that lets a family back into their booking, straight from a mail.

Signed rather than stored: nothing to clean up afterwards, and no row anybody
could guess the id of. It carries no expiry of its own because the event is the
expiry — a link to a date already run opens nothing.
"""

from datetime import timedelta

from django.conf import settings
from django.core import signing

SALT = "events.access"
CONTACT_SALT = "events.contact"


def token_for(event, email):
    return signing.dumps({"event": event.pk, "email": email}, salt=SALT)


def email_from_token(event, token):
    """The address the link was written to, or None if it is not this event's."""
    try:
        payload = signing.loads(token, salt=SALT)
    except signing.BadSignature:
        return None
    if payload.get("event") != event.pk:
        return None
    return payload.get("email")


def contact_token_for(email):
    """A link to everything one address booked, across events.

    Named for the address rather than an event, so it cannot borrow the event's
    date as its expiry the way `token_for` does: it carries its own.
    """
    return signing.dumps({"email": email}, salt=CONTACT_SALT)


def email_from_contact_token(token):
    """The address the link was written to, or None if it is stale or forged."""
    max_age = timedelta(days=settings.EVENTS_BOOKING_LINK_DAYS)
    try:
        payload = signing.loads(token, salt=CONTACT_SALT, max_age=max_age)
    except signing.BadSignature:
        # SignatureExpired is a BadSignature: an expired link and a forged one
        # are both simply not a way in.
        return None
    return payload.get("email")
