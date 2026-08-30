"""A From header a spam filter reads as a real sender, not a noreply blast.

A bare noreply@ address with no display name is one of the signals spam
filters weigh most heavily. Naming the association costs nothing and, paired
with a real Reply-To, gives every outbound mail the shape of something a
person sent.
"""

from django.conf import settings


def from_header(association):
    return f"{association.name} <{settings.DEFAULT_FROM_EMAIL}>"
