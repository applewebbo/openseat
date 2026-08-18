from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"
    # What the admin sidebar calls this app: volunteers read it, not developers.
    verbose_name = _("Events and bookings")
