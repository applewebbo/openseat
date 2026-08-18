import uuid
from datetime import timedelta

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

hex_colour = RegexValidator(
    r"^#[0-9A-Fa-f]{6}$", _("Use a six-digit hex colour, for example #ED5C08")
)


class SubjectType(models.TextChoices):
    SELF = "self", _("For myself")
    MINOR = "minor", _("For a minor child")
    PROTECTED = "protected", _("For a person I am the legal guardian of")


class SectionKey(models.TextChoices):
    SUBJECT = "subject", _("Who the application is for")
    APPLICANT = "applicant", _("Who is applying")
    MEMBER = "member", _("Member details")
    STATUTE = "statute", _("Statute and fee")
    PRIVACY = "privacy", _("Privacy notice")
    CONSENTS = "consents", _("Image consents")
    REVIEW = "review", _("Review and subscription")


# The catalogue an organiser switches on and off, in the only order that reads:
# the parental-responsibility declaration made in STATUTE governs CONSENTS, so it
# can never follow it.
SECTION_CATALOGUE = [
    SectionKey.SUBJECT,
    SectionKey.APPLICANT,
    SectionKey.MEMBER,
    SectionKey.STATUTE,
    SectionKey.PRIVACY,
    SectionKey.CONSENTS,
    SectionKey.REVIEW,
]

# Sections that only make sense when somebody applies on another person's behalf.
SECTIONS_FOR_OTHERS = {SectionKey.MEMBER}


class Association(models.Model):
    """The organisation the public form belongs to, with its own base colours."""

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), unique=True)
    street = models.CharField(_("street"), max_length=200)
    postcode = models.CharField(_("postcode"), max_length=5)
    city = models.CharField(_("city"), max_length=100)
    tax_code = models.CharField(_("tax code"), max_length=16)
    email = models.EmailField(_("email address"))
    statute_url = models.URLField(_("statute link"), blank=True)
    membership_fee = models.DecimalField(
        _("annual membership fee"), max_digits=7, decimal_places=2, default=0
    )
    logo = models.ImageField(_("logo"), upload_to="associations/", blank=True)
    colour_primary = models.CharField(
        _("primary colour"), max_length=7, default="#ED5C08", validators=[hex_colour]
    )
    colour_accent = models.CharField(
        _("accent colour"), max_length=7, default="#528116", validators=[hex_colour]
    )
    colour_neutral = models.CharField(
        _("neutral colour"), max_length=7, default="#4C5057", validators=[hex_colour]
    )

    class Meta:
        verbose_name = _("association")
        verbose_name_plural = _("associations")
        ordering = ("name",)

    def __str__(self):
        return self.name


class PublicForm(models.Model):
    """A public, login-free form: a membership application or an event booking."""

    association = models.ForeignKey(
        Association,
        verbose_name=_("association"),
        related_name="forms",
        on_delete=models.CASCADE,
    )
    slug = models.SlugField(_("slug"), unique=True)
    title = models.CharField(_("title"), max_length=200)
    intro = models.TextField(_("introduction"), blank=True)
    is_open = models.BooleanField(_("open"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("public form")
        verbose_name_plural = _("public forms")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.association.name} — {self.title}"

    def get_absolute_url(self):
        return reverse("intake:landing", kwargs={"slug": self.slug})

    def install_sections(self):
        """Give the form the whole catalogue; disabling is the organiser's job."""
        Section.objects.bulk_create(
            [
                Section(form=self, key=key, order=order)
                for order, key in enumerate(SECTION_CATALOGUE)
            ]
        )

    def path(self, subject_type):
        """The steps this applicant actually walks, in order.

        Until the opening question is answered the rest of the path is unknown,
        so only the opening step is on it.
        """
        enabled = [section.key for section in self.sections.all() if section.is_enabled]
        if not subject_type:
            return [key for key in enabled if key == SectionKey.SUBJECT]
        if subject_type == SubjectType.SELF:
            return [key for key in enabled if key not in SECTIONS_FOR_OTHERS]
        return enabled


class Section(models.Model):
    """One switchable step of a form."""

    form = models.ForeignKey(
        PublicForm,
        verbose_name=_("form"),
        related_name="sections",
        on_delete=models.CASCADE,
    )
    key = models.CharField(_("section"), max_length=20, choices=SectionKey)
    order = models.PositiveSmallIntegerField(_("order"), default=0)
    is_enabled = models.BooleanField(_("enabled"), default=True)

    class Meta:
        verbose_name = _("section")
        verbose_name_plural = _("sections")
        ordering = ("order",)
        constraints = [
            models.UniqueConstraint(fields=["form", "key"], name="unique_section_key")
        ]

    def __str__(self):
        return self.get_key_display()


class Submission(models.Model):
    """One person's answers, from the first keystroke to the signed request."""

    class State(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SUBMITTED = "submitted", _("Submitted")

    form = models.ForeignKey(
        PublicForm,
        verbose_name=_("form"),
        related_name="submissions",
        on_delete=models.CASCADE,
    )
    token = models.UUIDField(
        _("token"), default=uuid.uuid4, unique=True, editable=False
    )
    state = models.CharField(
        _("state"), max_length=10, choices=State, default=State.DRAFT
    )
    subject_type = models.CharField(
        _("applying for"), max_length=10, choices=SubjectType, blank=True
    )

    applicant_first_name = models.CharField(_("first name"), max_length=100, blank=True)
    applicant_last_name = models.CharField(_("last name"), max_length=100, blank=True)
    applicant_birth_date = models.DateField(_("date of birth"), null=True, blank=True)
    applicant_birth_place = models.CharField(
        _("place of birth"), max_length=100, blank=True
    )
    applicant_tax_code = models.CharField(_("tax code"), max_length=16, blank=True)
    applicant_street = models.CharField(_("street"), max_length=200, blank=True)
    applicant_number = models.CharField(_("number"), max_length=10, blank=True)
    applicant_postcode = models.CharField(_("postcode"), max_length=5, blank=True)
    applicant_city = models.CharField(_("city"), max_length=100, blank=True)
    applicant_phone = models.CharField(_("phone"), max_length=20, blank=True)
    applicant_email = models.EmailField(_("email address"), blank=True)

    member_first_name = models.CharField(_("first name"), max_length=100, blank=True)
    member_last_name = models.CharField(_("last name"), max_length=100, blank=True)
    member_birth_date = models.DateField(_("date of birth"), null=True, blank=True)
    member_birth_place = models.CharField(
        _("place of birth"), max_length=100, blank=True
    )
    member_tax_code = models.CharField(_("tax code"), max_length=16, blank=True)
    member_street = models.CharField(_("street"), max_length=200, blank=True)
    member_number = models.CharField(_("number"), max_length=10, blank=True)
    member_city = models.CharField(_("city"), max_length=100, blank=True)

    accepts_statute = models.BooleanField(_("accepts the statute"), default=False)
    # None until the declaration step is reached; the two answers are not
    # interchangeable with "unanswered", so this is deliberately nullable.
    sole_holder = models.BooleanField(
        _("sole holder of parental responsibility"), null=True, blank=True
    )
    second_parent_first_name = models.CharField(
        _("first name"), max_length=100, blank=True
    )
    second_parent_last_name = models.CharField(
        _("last name"), max_length=100, blank=True
    )
    second_parent_email = models.EmailField(_("email address"), blank=True)

    consent_images = models.BooleanField(_("image consent"), null=True, blank=True)
    consent_whatsapp = models.BooleanField(_("WhatsApp consent"), null=True, blank=True)

    # By the current statute you cannot attend without joining, so an
    # application may be the way somebody books a place. When the statute
    # changes, this is the link that stops being needed.
    event = models.ForeignKey(
        "events.Event",
        verbose_name=_("booked for"),
        related_name="applications",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reminder_sent_at = models.DateTimeField(_("reminded at"), null=True, blank=True)
    place = models.CharField(_("place"), max_length=100, blank=True)
    submitted_at = models.DateTimeField(_("submitted at"), null=True, blank=True)
    ip = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("submission")
        verbose_name_plural = _("submissions")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.member_display or _('draft')} — {self.form.title}"

    @property
    def member_display(self):
        """The person being enrolled: the child when there is one, else the signer."""
        if self.subject_type and self.subject_type != SubjectType.SELF:
            return f"{self.member_first_name} {self.member_last_name}".strip()
        return f"{self.applicant_first_name} {self.applicant_last_name}".strip()

    @property
    def applies_for_someone_else(self):
        return bool(self.subject_type) and self.subject_type != SubjectType.SELF

    @property
    def needs_second_parent(self):
        """Two holders of parental responsibility means two consents to collect."""
        return self.applies_for_someone_else and self.sole_holder is not True

    @property
    def image_consent_active(self):
        """Diffusion is off until every holder has said yes. In doubt, do not publish."""
        if not self.consent_images:
            return False
        if not self.needs_second_parent:
            return True
        return self.subscriptions.filter(
            role=Subscription.Role.SECOND_PARENT,
            subject=Subscription.Subject.IMAGE_CONSENT,
            state=Subscription.State.SIGNED,
        ).exists()

    @property
    def expires_at(self):
        """Thirty days from the last change, not from the first keystroke."""
        return self.updated_at + timedelta(days=settings.INTAKE_DRAFT_EXPIRY_DAYS)

    @property
    def is_expired(self):
        return self.state == self.State.DRAFT and timezone.now() >= self.expires_at

    def path(self):
        return self.form.path(self.subject_type)


class Subscription(models.Model):
    """One signature: who signed what, when, and from where."""

    class Role(models.TextChoices):
        PRIMARY = "primary", _("Applicant")
        SECOND_PARENT = "second_parent", _("Second holder of parental responsibility")

    class Subject(models.TextChoices):
        MEMBERSHIP = "membership", _("Membership application")
        IMAGE_CONSENT = "image_consent", _("Image consent")

    class State(models.TextChoices):
        PENDING = "pending", _("Awaiting signature")
        SIGNED = "signed", _("Signed")
        DECLINED = "declined", _("Declined")

    submission = models.ForeignKey(
        Submission,
        verbose_name=_("submission"),
        related_name="subscriptions",
        on_delete=models.CASCADE,
    )
    signatory_name = models.CharField(_("signatory"), max_length=200)
    signatory_email = models.EmailField(_("email address"), blank=True)
    role = models.CharField(_("role"), max_length=20, choices=Role)
    subject = models.CharField(_("subject"), max_length=20, choices=Subject)
    state = models.CharField(
        _("state"), max_length=10, choices=State, default=State.PENDING
    )
    token = models.UUIDField(
        _("token"), default=uuid.uuid4, unique=True, editable=False
    )
    declaration = models.TextField(_("declaration"), blank=True)
    signed_at = models.DateTimeField(_("signed at"), null=True, blank=True)
    ip = models.GenericIPAddressField(_("IP address"), null=True, blank=True)

    class Meta:
        verbose_name = _("subscription")
        verbose_name_plural = _("subscriptions")
        ordering = ("submission", "role")

    def __str__(self):
        return f"{self.signatory_name} — {self.get_subject_display()}"
