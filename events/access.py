"""The link that lets a family back into their booking, straight from a mail.

Signed rather than stored: nothing to clean up afterwards, and no row anybody
could guess the id of. It carries no expiry of its own because the event is the
expiry — a link to a date already run opens nothing.
"""

from django.core import signing

SALT = "events.access"


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
