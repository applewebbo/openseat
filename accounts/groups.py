"""The roles a volunteer can be given, as groups the admin reads."""

from django.contrib.auth.models import Group, Permission

EDITORS = "Editor"

# What an editor may touch, model by model. Booking is deliberately short of
# delete: a place is withdrawn with Booking.cancel(), which keeps the row and
# says when it happened, while deleting loses who had booked at all.
EDITOR_PERMISSIONS = {
    ("events", "event"): ("add", "change", "delete", "view"),
    ("events", "booking"): ("add", "change", "view"),
}


def ensure_editor_group():
    """Create the editor group, or reset it to what it is defined to be.

    Idempotent, and run at every deploy: the group is a definition rather than
    a starting point, so a permission granted by hand in the admin is taken
    back rather than accumulating unnoticed.
    """
    group, _created = Group.objects.get_or_create(name=EDITORS)
    wanted = [
        Permission.objects.get(
            content_type__app_label=app_label,
            content_type__model=model,
            codename=f"{action}_{model}",
        )
        for (app_label, model), actions in EDITOR_PERMISSIONS.items()
        for action in actions
    ]
    group.permissions.set(wanted)
    return group
