from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from intake.models import Association
from members.models import Member


class EventQuerySet(models.QuerySet):
    def due_for_checklist(self):
        """Events starting today whose list has not gone out yet.

        The list is a door checklist, not a report: it must be in somebody's
        hands before the event, so it goes at midnight of the event day.
        """
        today = timezone.localdate()
        return self.filter(
            is_published=True,
            starts_at__date=today,
            checklist_sent_at__isnull=True,
        )


class Event(models.Model):
    """Something the association runs, that members book a place at."""

    association = models.ForeignKey(
        Association,
        verbose_name=_("association"),
        related_name="events",
        on_delete=models.CASCADE,
    )
    slug = models.SlugField(_("slug"), unique=True)
    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    location = models.CharField(_("location"), max_length=200, blank=True)
    starts_at = models.DateTimeField(_("starts at"))
    ends_at = models.DateTimeField(_("ends at"), null=True, blank=True)
    is_published = models.BooleanField(_("published"), default=True)
    checklist_sent_at = models.DateTimeField(
        _("checklist sent at"), null=True, blank=True
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ("starts_at",)

    def __str__(self):
        return f"{self.title} — {self.starts_at.strftime('%d/%m/%Y')}"

    def get_absolute_url(self):
        return reverse("events:landing", kwargs={"slug": self.slug})

    @property
    def is_open(self):
        """No capacity limit: the only thing that closes bookings is the clock."""
        return self.is_published and timezone.now() < self.starts_at


class BookingQuerySet(models.QuerySet):
    def confirmed(self):
        return self.filter(cancelled_at__isnull=True).order_by(
            "member__last_name", "member__first_name"
        )

    def book(self, event, member):
        """Book a place, reviving a cancelled booking rather than duplicating it."""
        booking, _created = self.get_or_create(event=event, member=member)
        if booking.cancelled_at is not None:
            booking.cancelled_at = None
            booking.save(update_fields=["cancelled_at"])
        return booking


class Booking(models.Model):
    """One member's place at one event."""

    event = models.ForeignKey(
        Event,
        verbose_name=_("event"),
        related_name="bookings",
        on_delete=models.CASCADE,
    )
    member = models.ForeignKey(
        Member,
        verbose_name=_("member"),
        related_name="bookings",
        on_delete=models.CASCADE,
    )
    note = models.TextField(_("note"), blank=True)
    created_at = models.DateTimeField(_("booked at"), auto_now_add=True)
    cancelled_at = models.DateTimeField(_("cancelled at"), null=True, blank=True)

    objects = BookingQuerySet.as_manager()

    class Meta:
        verbose_name = _("booking")
        verbose_name_plural = _("bookings")
        ordering = ("member__last_name", "member__first_name")
        constraints = [
            models.UniqueConstraint(
                fields=["event", "member"], name="one_booking_per_member"
            )
        ]

    def __str__(self):
        return f"{self.member.full_name} — {self.event.title}"

    def cancel(self):
        self.cancelled_at = timezone.now()
        self.save(update_fields=["cancelled_at"])
