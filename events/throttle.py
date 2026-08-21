"""One send per address per window.

The Bookings card is a public form that puts mail in somebody's inbox, and the
address it mails is the one typed into it — so without a limit anybody can use
it to flood a stranger. Kept in the cache rather than the database: a rate
limit is a fact about the last few minutes, not a record worth keeping.
"""

import hashlib

from django.conf import settings
from django.core.cache import cache

PREFIX = "events.booking-link"


def _key(email):
    """Hashed, so the cache never holds a plain address of somebody's."""
    digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
    return f"{PREFIX}:{digest}"


def claim_send(email):
    """True the first time this address asks, False until the window is out."""
    seconds = settings.EVENTS_BOOKING_LINK_THROTTLE_SECONDS
    # add() writes only when the key is absent, and answers whether it wrote:
    # check and claim in one step, so two requests at once cannot both win.
    return cache.add(_key(email), True, timeout=seconds)
