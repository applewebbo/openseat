from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from events.models import Booking, Event


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    autocomplete_fields = ("member",)
    fields = ("member", "note", "created_at", "cancelled_at")
    readonly_fields = ("created_at",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "starts_at", "association", "booked", "checklist_sent_at")
    list_filter = ("association", "is_published")
    date_hierarchy = "starts_at"
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("checklist_sent_at",)
    inlines = [BookingInline]

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
