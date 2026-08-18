from django.apps import AppConfig


class OpsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ops"

    def ready(self):
        from ops import checks  # noqa: F401  (registers the deploy check)
