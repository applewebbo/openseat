"""What every page knows about the build it is served by."""

from django.conf import settings

from intake.models import Association


def build(request):
    """The vendor and version the footer signs itself with."""
    return {
        "app_vendor": settings.APP_VENDOR,
        "app_vendor_url": settings.APP_VENDOR_URL,
        "app_version": settings.APP_VERSION,
        "app_source_url": settings.APP_SOURCE_URL,
    }


def association(request):
    """The singleton, for pages that never think to ask for it themselves.

    Views that already pass their own `association` — home, the form engine —
    take precedence: this only fills the gap for third-party views such as
    allauth's, which render no context of their own.
    """
    return {"association": Association.current()}
