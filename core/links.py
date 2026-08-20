"""Links that outlive the request that made them."""

from django.conf import settings
from django.urls import reverse


def absolute_url(viewname, *args, **kwargs):
    """A link fit for an email, where there is no request to read the host from.

    Deliberately a setting rather than django.contrib.sites: one deployment
    serves one association, and a row in a table is a second place to get it
    wrong.
    """
    return f"{settings.SITE_BASE_URL}{reverse(viewname, args=args, kwargs=kwargs)}"
