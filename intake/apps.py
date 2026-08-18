from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IntakeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "intake"
    # What the admin sidebar calls this app: volunteers read it, not developers.
    verbose_name = _("Association and applications")
