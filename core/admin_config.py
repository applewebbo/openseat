from django.contrib.admin.apps import AdminConfig


class OpenSeatAdminConfig(AdminConfig):
    """Installed in place of django.contrib.admin, so every ModelAdmin keeps
    registering against `admin.site` and lands on the project's site anyway.

    It is not in core/apps.py: Django scans that module for the app config of
    `core` itself, and would find three candidates there — this one, the
    imported AdminConfig, and core's own.
    """

    default_site = "core.admin.OpenSeatAdminSite"
