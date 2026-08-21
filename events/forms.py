from django import forms
from django.utils.translation import gettext_lazy as _

from events.models import Booking
from intake.validators import validate_tax_code
from members.models import Member


class IdentifyForm(forms.Form):
    """Email plus tax code, so a guessed address alone reveals nobody.

    Names on the register belong to minors: the pair has to prove the person
    asking is the family before any of them is shown.
    """

    template_name = "intake/forms/section-form.html"

    email = forms.EmailField(
        label=_("Email address"),
        help_text=_("The one the association writes to."),
        widget=forms.EmailInput(
            attrs={"class": "input input-bordered w-full", "inputmode": "email"}
        ),
    )
    tax_code = forms.CharField(
        label=_("Tax code"),
        help_text=_("Of one of the members registered at that address."),
        max_length=16,
        validators=[validate_tax_code],
        widget=forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "autocapitalize": "characters",
            }
        ),
    )

    def __init__(self, *args, association=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.association = association

    def clean(self):
        cleaned = super().clean()
        email, tax_code = cleaned.get("email"), cleaned.get("tax_code")
        if not (email and tax_code):
            return cleaned

        household = Member.objects.for_contact(self.association, email)
        if not household.filter(tax_code__iexact=tax_code.strip()).exists():
            # One message for both halves: saying which was wrong would let
            # somebody test addresses against the register.
            raise forms.ValidationError(
                _(
                    "No member is registered with this pair. Check the tax code, "
                    "or apply to join below."
                )
            )
        cleaned["household"] = household
        return cleaned


class BookingContactForm(forms.ModelForm):
    """What can be changed from the mail link: how to reach them, and a note.

    Not the name, tax code or consents — those belong to the signed
    application, or to the register once the booking is confirmed.
    """

    template_name = "intake/forms/section-form.html"

    class Meta:
        model = Booking
        fields = ["contact_name", "contact_email", "contact_phone", "note"]
        widgets = {
            "contact_name": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "contact_email": forms.EmailInput(
                attrs={"class": "input input-bordered w-full", "inputmode": "email"}
            ),
            "contact_phone": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "note": forms.Textarea(
                attrs={"class": "textarea textarea-bordered w-full", "rows": 3}
            ),
        }
