from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    # What the admin sidebar calls this app: volunteers read it, not developers.
    verbose_name = _("Back-office users")

    def ready(self):
        from accounts import signals  # noqa: F401  (registers the approval gate)
