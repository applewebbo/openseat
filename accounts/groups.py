"""The roles a volunteer can be given, as groups the admin reads."""

from django.contrib.auth.models import Group, Permission

EDITORS = "Editor"
SENIOR_EDITORS = "Editor+"

# What an editor may touch, model by model. Booking is deliberately short of
# delete: a place is withdrawn with Booking.cancel(), which keeps the row and
# says when it happened, while deleting loses who had booked at all.
EDITOR_PERMISSIONS = {
    ("events", "event"): ("add", "change", "delete", "view"),
    ("events", "booking"): ("add", "change", "view"),
}

# On top of everything an editor has: exporting the register is sensitive
# enough that not every volunteer at the door should get it for free.
SENIOR_EDITOR_PERMISSIONS = {
    ("events", "event"): ("export_members",),
}


def _permissions_for(mapping):
    return [
        Permission.objects.get(
            content_type__app_label=app_label,
            content_type__model=model,
            codename=f"{action}_{model}",
        )
        for (app_label, model), actions in mapping.items()
        for action in actions
    ]


def _custom_permissions_for(mapping):
    return [
        Permission.objects.get(
            content_type__app_label=app_label,
            content_type__model=model,
            codename=codename,
        )
        for (app_label, model), codenames in mapping.items()
        for codename in codenames
    ]


def ensure_editor_group():
    """Create the editor group, or reset it to what it is defined to be.

    Idempotent, and run at every deploy: the group is a definition rather than
    a starting point, so a permission granted by hand in the admin is taken
    back rather than accumulating unnoticed.
    """
    group, _created = Group.objects.get_or_create(name=EDITORS)
    group.permissions.set(_permissions_for(EDITOR_PERMISSIONS))
    return group


def ensure_senior_editor_group():
    """Editor+: everything an editor can do, plus exporting event members."""
    group, _created = Group.objects.get_or_create(name=SENIOR_EDITORS)
    group.permissions.set(
        _permissions_for(EDITOR_PERMISSIONS)
        + _custom_permissions_for(SENIOR_EDITOR_PERMISSIONS)
    )
    return group
