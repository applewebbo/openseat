from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Django 6.1's own Italian catalogue has no translation yet for this
        # new constant, so every blank choice/FK select falls back to English.
        # Overwriting it here is the extension point Django's own source
        # comment invites ("This allows any app's ready() method to overwrite
        # BLANK_CHOICE_LABEL").
        from django.db.models import fields

        fields.BLANK_CHOICE_LABEL = _("Choose an option")
