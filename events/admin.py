from django import forms
from django.contrib import admin
from django.db.models import Count, Q
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _

from events.models import Booking, Event
from events.notifications import send_booking_confirmation
from intake.models import PublicForm


def _short(moment):
    """A datetime the way the locale writes it short: 20/04/2026 16:00."""
    if moment is None:
        return None
    return formats.date_format(timezone.localtime(moment), "SHORT_DATETIME_FORMAT")


def _confirm_if_new(booking, created, send_confirmation):
    """The same mail a public booking gets, sent once — on the way in."""
    if (
        created
        and send_confirmation
        and booking.contact_email
        and booking.cancelled_at is None
    ):
        send_booking_confirmation(booking.event, booking.contact_email)


class BookingAdminForm(forms.ModelForm):
    # Not a model field: a one-time switch for this save, on by default —
    # an editor unticks it only for the rare booking that should stay quiet.
    send_confirmation = forms.BooleanField(
        label=_("Send the confirmation mail"), required=False, initial=True
    )

    class Meta:
        model = Booking
        fields = "__all__"


class BookingInline(admin.TabularInline):
    model = Booking
    form = BookingAdminForm
    extra = 0
    autocomplete_fields = ("member",)
    fields = (
        "first_name",
        "last_name",
        "member",
        "contact_name",
        "contact_email",
        "contact_phone",
        "send_confirmation",
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
    readonly_fields = ("checklist_sent_at",)
    inlines = [BookingInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "form":
            kwargs["queryset"] = PublicForm.objects.filter(is_open=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_formset(self, request, form, formset, change):
        if formset.model is not Booking:
            formset.save()
            return
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for obj, booking_form in zip(instances, formset.saved_forms, strict=True):
            created = obj.pk is None
            obj.save()
            _confirm_if_new(
                obj, created, booking_form.cleaned_data.get("send_confirmation", True)
            )
        formset.save_m2m()

    def get_queryset(self, request):
        # One annotated count instead of one `.count()` query per row — the
        # changelist would otherwise pay for an extra query per event shown.
        return (
            super()
            .get_queryset(request)
            .annotate(
                booked_count=Count(
                    "bookings", filter=Q(bookings__cancelled_at__isnull=True)
                )
            )
        )

    @admin.display(description=_("date"), ordering="starts_at")
    def starts_on(self, obj):
        """The short format: a list is scanned, and the weekday is noise in it."""
        return _short(obj.starts_at)

    @admin.display(description=_("sent"), ordering="checklist_sent_at")
    def sent_on(self, obj):
        return _short(obj.checklist_sent_at)

    @admin.display(description=_("booked"), ordering="booked_count")
    def booked(self, obj):
        """Confirmed places, cancellations excluded. Never a capacity gate."""
        return obj.booked_count


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
    form = BookingAdminForm
    autocomplete_fields = ("member",)
    readonly_fields = ("submission", "created_at")

    def save_model(self, request, obj, form, change):
        created = obj.pk is None
        super().save_model(request, obj, form, change)
        _confirm_if_new(obj, created, form.cleaned_data.get("send_confirmation", True))

    @admin.display(description=_("name"), ordering="last_name")
    def full_name(self, obj):
        return obj.full_name
