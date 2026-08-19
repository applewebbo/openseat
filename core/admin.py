"""The admin as the association's own back office rather than a generic one."""

from django.contrib import admin

from intake.models import Association

# The order the work happens in: what is done weekly first, what is set up once
# after it, and the machinery nobody opens on purpose last. Django orders apps
# alphabetically, which puts allauth's tables above the register.
APP_ORDER = ["events", "members", "intake", "accounts"]


class OpenSeatAdminSite(admin.AdminSite):
    """Carries the association into every admin page, login included."""

    # What a fresh install is called, before anybody has said who they are.
    site_header = "OpenSeat"
    site_title = "OpenSeat"

    def each_context(self, request):
        """Read the singleton per request.

        Not a `site_header` attribute: that is read at import time, when the
        database may not exist yet — a fresh clone would crash before its first
        migrate.
        """
        context = super().each_context(request)
        association = Association.current()
        context["association"] = association
        if association is not None:
            context["site_header"] = association.name
        return context

    def get_app_list(self, request, app_label=None):
        apps = super().get_app_list(request, app_label)
        return sorted(
            apps,
            key=lambda app: (
                APP_ORDER.index(app["app_label"])
                if app["app_label"] in APP_ORDER
                else len(APP_ORDER)
            ),
        )
