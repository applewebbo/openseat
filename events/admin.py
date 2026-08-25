from django.contrib import admin
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _

from events.models import Booking, Event
from intake.models import PublicForm


def _short(moment):
    """A datetime the way the locale writes it short: 20/04/2026 16:00."""
    if moment is None:
        return None
    return formats.date_format(timezone.localtime(moment), "SHORT_DATETIME_FORMAT")


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    autocomplete_fields = ("member",)
    fields = (
        "first_name",
        "last_name",
        "member",
        "confirmed_on",
        "fee_amount",
        "fee_method",
        "cancelled_at",
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # No association column or filter: one installation holds one, so the same
    # name on every row only takes space away from the title.
    list_display = ("title", "starts_on", "booked", "cost", "sent_on")
    list_filter = ("is_published",)
    date_hierarchy = "starts_at"
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("checklist_sent_at",)
    inlines = [BookingInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "form":
            kwargs["queryset"] = PublicForm.objects.filter(is_open=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        return obj.bookings.active().count()


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("full_name", "event", "confirmed_on", "cancelled_at")
    list_filter = ("event",)
    search_fields = (
        "first_name",
        "last_name",
        "member__last_name",
        "member__first_name",
    )
    autocomplete_fields = ("member",)
    readonly_fields = ("submission", "created_at")

    @admin.display(description=_("name"), ordering="last_name")
    def full_name(self, obj):
        return obj.full_name
