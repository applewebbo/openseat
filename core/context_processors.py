"""What every page knows about the build it is served by."""

from django.conf import settings


def build(request):
    """The vendor and version the footer signs itself with."""
    return {
        "app_vendor": settings.APP_VENDOR,
        "app_vendor_url": settings.APP_VENDOR_URL,
        "app_version": settings.APP_VERSION,
        "app_source_url": settings.APP_SOURCE_URL,
    }
