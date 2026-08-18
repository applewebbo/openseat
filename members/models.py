from django.db import models
from django.utils.translation import gettext_lazy as _

from intake.models import Association, Submission


class MemberQuerySet(models.QuerySet):
    def for_contact(self, association, email):
        """Everyone this address may book for: a parent can have two children."""
        return self.filter(
            association=association,
            contact_email__iexact=(email or "").strip(),
            is_active=True,
        )


class Member(models.Model):
    """An entry in the register — the libro soci, not the request that made it.

    Deliberately a copy of the application's data rather than a view onto it: the
    signed request is a document that must not change, while the register is
    corrected, updated and kept for years after.
    """

    association = models.ForeignKey(
        Association,
        verbose_name=_("association"),
        related_name="members",
        on_delete=models.CASCADE,
    )
    submission = models.OneToOneField(
        Submission,
        verbose_name=_("application"),
        related_name="member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Empty for members entered by hand from a paper form."),
    )

    first_name = models.CharField(_("first name"), max_length=100)
    last_name = models.CharField(_("last name"), max_length=100)
    birth_date = models.DateField(_("date of birth"), null=True, blank=True)
    birth_place = models.CharField(_("place of birth"), max_length=100, blank=True)
    tax_code = models.CharField(_("tax code"), max_length=16, blank=True)
    street = models.CharField(_("street"), max_length=200, blank=True)
    number = models.CharField(_("number"), max_length=10, blank=True)
    postcode = models.CharField(_("postcode"), max_length=5, blank=True)
    city = models.CharField(_("city"), max_length=100, blank=True)
    email = models.EmailField(_("email address"), blank=True)

    # Who the association actually writes to: the member when of age, the parent
    # or guardian otherwise. Bookings are looked up by this address.
    contact_name = models.CharField(_("contact"), max_length=200, blank=True)
    contact_email = models.EmailField(_("contact email"))
    contact_phone = models.CharField(_("contact phone"), max_length=20, blank=True)

    joined_on = models.DateField(_("joined on"), auto_now_add=True)
    ratified_on = models.DateField(
        _("ratified on"),
        null=True,
        blank=True,
        help_text=_("When the board minuted the admission."),
    )
    is_active = models.BooleanField(_("active"), default=True)

    objects = MemberQuerySet.as_manager()

    class Meta:
        verbose_name = _("member")
        verbose_name_plural = _("members")
        ordering = ("last_name", "first_name")
        indexes = [models.Index(fields=["association", "contact_email"])]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
