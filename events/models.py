from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.images import square_from, square_name
from intake.models import Association, PublicForm, Submission
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
    form = models.ForeignKey(
        PublicForm,
        verbose_name=_("application form"),
        related_name="events",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_(
            "Booked through when set. Unset falls back to the association's "
            "newest open form."
        ),
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
    checkin_started_at = models.DateTimeField(
        _("check-in started at"),
        null=True,
        blank=True,
        help_text=_(
            "Set by an editor at the door. Closes public bookings until cleared."
        ),
    )
    cost = models.DecimalField(
        _("suggested cost"),
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Not shown to the public yet."),
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
        """No capacity limit: what closes bookings is the clock, or an editor
        opening check-in at the door — whichever comes first."""
        return (
            self.is_published
            and self.checkin_started_at is None
            and timezone.now() < self.starts_at
        )

    @property
    def is_checkin_open(self):
        return self.checkin_started_at is not None


class FeeMethod(models.TextChoices):
    CASH = "cash", _("Cash")
    TRANSFER = "transfer", _("Bank transfer")
    OTHER = "other", _("Other")


class BookingQuerySet(models.QuerySet):
    def active(self):
        """A place still held — cancelled or not, confirmed or not."""
        return self.filter(cancelled_at__isnull=True).order_by(
            "last_name", "first_name"
        )

    def unconfirmed(self):
        """Nobody said they turned up and paid, so no register entry was earned."""
        return self.filter(confirmed_on__isnull=True)

    def for_contact(self, email):
        return self.filter(contact_email__iexact=(email or "").strip())

    def upcoming(self):
        """Places at dates still to come, soonest first.

        What a booking page can still act on: a date already run takes no
        cancellation and no change of contacts.
        """
        return self.filter(
            event__is_published=True, event__starts_at__gt=timezone.now()
        ).order_by("event__starts_at", "last_name", "first_name")

    def book(self, event, member):
        """A place for somebody already on the register.

        Reviving a cancelled booking rather than duplicating it: they are a
        member either way, so nothing has to be signed a second time.
        """
        booking, _created = self.get_or_create(
            event=event,
            member=member,
            defaults={
                "first_name": member.first_name,
                "last_name": member.last_name,
                "contact_name": member.contact_name,
                "contact_email": member.contact_email,
                "contact_phone": member.contact_phone,
            },
        )
        if booking.cancelled_at is not None:
            booking.cancelled_at = None
            booking.save(update_fields=["cancelled_at"])
        return booking

    def book_application(self, event, submission):
        """A place for somebody the register does not hold yet.

        The signed application is all there is to go on, and it stays a
        document: the booking copies out of it and is edited on its own.
        """
        return self.create(
            event=event,
            submission=submission,
            first_name=submission.subject_first_name,
            last_name=submission.subject_last_name,
            contact_name=submission.applicant_name,
            contact_email=submission.applicant_email,
            contact_phone=submission.applicant_phone,
        )


class Booking(models.Model):
    """One person's place at one event — a booking, not a membership.

    The statute says you cannot attend without joining, but you join by turning
    up, paying the fee and having the association say so. Until that happens the
    booking carries its own copy of who is coming and who to write to, and
    `member` is empty: there is no register entry to point at yet.
    """

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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Filled in when the booking is confirmed."),
    )
    submission = models.OneToOneField(
        Submission,
        verbose_name=_("application"),
        related_name="booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    first_name = models.CharField(_("first name"), max_length=100)
    last_name = models.CharField(_("last name"), max_length=100)
    contact_name = models.CharField(_("contact"), max_length=200, blank=True)
    contact_email = models.EmailField(_("contact email"))
    contact_phone = models.CharField(_("contact phone"), max_length=20, blank=True)

    note = models.TextField(_("note"), blank=True)

    confirmed_on = models.DateField(
        _("confirmed on"),
        null=True,
        blank=True,
        help_text=_("The day they turned up and paid the fee."),
    )
    fee_amount = models.DecimalField(
        _("fee paid"), max_digits=7, decimal_places=2, null=True, blank=True
    )
    fee_method = models.CharField(
        _("paid by"), max_length=10, choices=FeeMethod, blank=True
    )

    created_at = models.DateTimeField(_("booked at"), auto_now_add=True)
    cancelled_at = models.DateTimeField(_("cancelled at"), null=True, blank=True)

    objects = BookingQuerySet.as_manager()

    class Meta:
        verbose_name = _("booking")
        verbose_name_plural = _("bookings")
        ordering = ("last_name", "first_name")
        constraints = [
            models.UniqueConstraint(
                fields=["event", "member"],
                condition=models.Q(member__isnull=False),
                name="one_booking_per_member",
            )
        ]

    def __str__(self):
        return f"{self.full_name} — {self.event.title}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_confirmed(self):
        return self.confirmed_on is not None

    def save(self, *args, **kwargs):
        """Confirming attendance is joining: the register entry is made here.

        A booking already tied to a member is already on the register — the
        already-a-member path books nobody twice.
        """
        if self.confirmed_on and self.member_id is None and self.submission_id:
            from members.register import enrol

            self.member = enrol(self.submission)
        super().save(*args, **kwargs)

    def cancel(self):
        self.cancelled_at = timezone.now()
        self.save(update_fields=["cancelled_at"])
