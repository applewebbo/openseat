from django.contrib import admin
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _

from events.models import Booking, Event


def _short(moment):
    """A datetime the way the locale writes it short: 20/04/2026 16:00."""
    if moment is None:
        return None
    return formats.date_format(timezone.localtime(moment), "SHORT_DATETIME_FORMAT")


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    autocomplete_fields = ("member",)
    fields = ("member", "note", "created_at", "cancelled_at")
    readonly_fields = ("created_at",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # No association column or filter: one installation holds one, so the same
    # name on every row only takes space away from the title.
    list_display = ("title", "starts_on", "booked", "sent_on")
    list_filter = ("is_published",)
    date_hierarchy = "starts_at"
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("checklist_sent_at",)
    inlines = [BookingInline]

    @admin.display(description=_("date"), ordering="starts_at")
    def starts_on(self, obj):
        """The short format: a list is scanned, and the weekday is noise in it."""
        return _short(obj.starts_at)

    @admin.display(description=_("sent"), ordering="checklist_sent_at")
    def sent_on(self, obj):
        return _short(obj.checklist_sent_at)

    @admin.display(description=_("booked"))
    def booked(self, obj):
        """Confirmed places, cancellations excluded. Never a capacity gate."""
        return obj.bookings.confirmed().count()


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("member", "event", "created_at", "cancelled_at")
    list_filter = ("event",)
    search_fields = ("member__last_name", "member__first_name")
    autocomplete_fields = ("member",)
