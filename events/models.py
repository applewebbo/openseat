from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.images import square_from, square_name
from intake.models import Association
from members.models import Member

DEFAULT_WIDE = "img/event-default-wide.jpg"
DEFAULT_SQUARE = "img/event-default-square.jpg"


class EventQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def upcoming(self):
        """Still to happen, soonest first — the order the home page reads in."""
        return (
            self.published().filter(starts_at__gt=timezone.now()).order_by("starts_at")
        )

    def past(self):
        """Already run, newest first: the archive is read backwards."""
        return (
            self.published()
            .filter(starts_at__lte=timezone.now())
            .order_by("-starts_at")
        )

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
    image = models.ImageField(
        _("image"),
        upload_to="events/",
        blank=True,
        help_text=_("A wide picture, 1200 px or more. The square one is cut from it."),
    )
    image_square = models.ImageField(
        _("square image"), upload_to="events/", blank=True, editable=False
    )
    square_source = models.CharField(max_length=100, blank=True, editable=False)
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

    def save(self, *args, **kwargs):
        """Keep the square picture in step with the wide one it is cut from."""
        super().save(*args, **kwargs)
        if self.image:
            # The name the storage gave the square file may carry a suffix of its
            # own, so what it was cut from is recorded rather than guessed back.
            if self.square_source != self.image.name:
                self.image_square.save(
                    square_name(self.image.name), square_from(self.image), save=False
                )
                self.square_source = self.image.name
                super().save(update_fields=["image_square", "square_source"])
        elif self.image_square or self.square_source:
            self.image_square = ""
            self.square_source = ""
            super().save(update_fields=["image_square", "square_source"])

    @property
    def wide_url(self):
        return self.image.url if self.image else static(DEFAULT_WIDE)

    @property
    def square_url(self):
        return self.image_square.url if self.image_square else static(DEFAULT_SQUARE)

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
