from datetime import datetime

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import Booking, Event
from intake.models import PublicForm, SubjectType
from intake.validators import validate_phone, validate_postcode, validate_tax_code
from members.models import Member

_TEXT = {"class": "input input-bordered w-full"}
_DATE = {"type": "date", "class": "input input-bordered w-full"}
_CHECKBOX = {"class": "checkbox checkbox-primary mt-0.5 [--radius-selector:0.25rem]"}
_RADIO = {"class": "radio radio-primary mt-0.5"}


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


class RecoverForm(forms.Form):
    """The address, and nothing else.

    No tax code: the link goes to the inbox, so holding the inbox is already
    the proof. Asking for more would only lock out whoever booked through the
    public form, who is on no register to be checked against.
    """

    template_name = "intake/forms/section-form.html"

    email = forms.EmailField(
        label=_("Email address"),
        widget=forms.EmailInput(
            attrs={
                "class": "input input-bordered w-full",
                "inputmode": "email",
                "autocomplete": "email",
            }
        ),
    )


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


class ManualBookingForm(forms.Form):
    """A booking entered by an editor from a paper form signed at the door.

    One page instead of the public wizard's steps, and consents are plain
    checkboxes: the paper is already signed, so there is no second-parent
    email round trip to model here.
    """

    subject_type = forms.ChoiceField(
        label=_("Applying for"),
        choices=SubjectType.choices,
        widget=forms.RadioSelect(attrs=_RADIO),
        initial=SubjectType.MINOR,
    )

    applicant_first_name = forms.CharField(
        label=_("First name"), max_length=100, widget=forms.TextInput(attrs=_TEXT)
    )
    applicant_last_name = forms.CharField(
        label=_("Last name"), max_length=100, widget=forms.TextInput(attrs=_TEXT)
    )
    applicant_birth_date = forms.DateField(
        label=_("Date of birth"),
        widget=forms.DateInput(attrs=_DATE, format="%Y-%m-%d"),
    )
    applicant_birth_place = forms.CharField(
        label=_("Place of birth"), max_length=100, widget=forms.TextInput(attrs=_TEXT)
    )
    applicant_tax_code = forms.CharField(
        label=_("Tax code"),
        max_length=16,
        validators=[validate_tax_code],
        widget=forms.TextInput(attrs={**_TEXT, "autocapitalize": "characters"}),
    )
    applicant_street = forms.CharField(
        label=_("Street"), max_length=200, widget=forms.TextInput(attrs=_TEXT)
    )
    applicant_number = forms.CharField(
        label=_("Number"), max_length=10, widget=forms.TextInput(attrs=_TEXT)
    )
    applicant_postcode = forms.CharField(
        label=_("Postcode"),
        max_length=5,
        validators=[validate_postcode],
        widget=forms.TextInput(attrs={**_TEXT, "inputmode": "numeric"}),
    )
    applicant_city = forms.CharField(
        label=_("City"), max_length=100, widget=forms.TextInput(attrs=_TEXT)
    )
    applicant_phone = forms.CharField(
        label=_("Phone"),
        max_length=20,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={**_TEXT, "inputmode": "tel"}),
    )
    applicant_email = forms.EmailField(
        label=_("Email address"),
        widget=forms.EmailInput(attrs={**_TEXT, "inputmode": "email"}),
    )

    member_first_name = forms.CharField(
        label=_("First name"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=_TEXT),
    )
    member_last_name = forms.CharField(
        label=_("Last name"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=_TEXT),
    )
    member_birth_date = forms.DateField(
        label=_("Date of birth"),
        required=False,
        widget=forms.DateInput(attrs=_DATE, format="%Y-%m-%d"),
    )
    member_birth_place = forms.CharField(
        label=_("Place of birth"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=_TEXT),
    )
    member_tax_code = forms.CharField(
        label=_("Tax code"),
        max_length=16,
        required=False,
        widget=forms.TextInput(attrs={**_TEXT, "autocapitalize": "characters"}),
    )
    member_street = forms.CharField(
        label=_("Street"),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs=_TEXT),
    )
    member_number = forms.CharField(
        label=_("Number"),
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs=_TEXT),
    )
    member_city = forms.CharField(
        label=_("City"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=_TEXT),
    )

    accepts_statute = forms.BooleanField(
        required=True,
        label=_("Form signed"),
        widget=forms.CheckboxInput(attrs=_CHECKBOX),
    )
    sole_holder = forms.BooleanField(
        required=False,
        label=_("Sole holder of parental responsibility"),
        widget=forms.CheckboxInput(attrs=_CHECKBOX),
    )
    second_parent_first_name = forms.CharField(
        label=_("Other parent's first name"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=_TEXT),
    )
    second_parent_last_name = forms.CharField(
        label=_("Other parent's last name"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=_TEXT),
    )

    consent_images = forms.BooleanField(
        required=False,
        label=_("Image consent"),
        widget=forms.CheckboxInput(attrs=_CHECKBOX),
    )
    consent_whatsapp = forms.BooleanField(
        required=False,
        label=_("WhatsApp consent"),
        widget=forms.CheckboxInput(attrs=_CHECKBOX),
    )

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    def clean(self):
        cleaned = super().clean()
        for name, value in cleaned.items():
            if name.endswith("_tax_code") and value:
                cleaned[name] = value.upper()

        subject_type = cleaned.get("subject_type")
        applies_for_someone_else = (
            bool(subject_type) and subject_type != SubjectType.SELF
        )
        if applies_for_someone_else:
            for name in (
                "member_first_name",
                "member_last_name",
                "member_birth_date",
                "member_tax_code",
            ):
                if not cleaned.get(name):
                    self.add_error(name, _("This field is required."))
            if not cleaned.get("sole_holder"):
                for name in ("second_parent_first_name", "second_parent_last_name"):
                    if not cleaned.get(name):
                        self.add_error(name, _("This field is required."))
        return cleaned


class EventCreateForm(forms.ModelForm):
    """An editor's own way in, next to the admin. No slug: that is generated,
    never typed, and the association is always this installation's own."""

    template_name = "events/create-form.html"

    field_order = [
        "title",
        "description",
        "location",
        "starts_date",
        "starts_time",
        "image",
        "cost",
        "is_published",
        "form",
    ]

    starts_date = forms.DateField(label=_("Date"), widget=forms.DateInput(attrs=_DATE))
    starts_time = forms.TimeField(
        label=_("Time"),
        input_formats=["%H:%M"],
        widget=forms.TimeInput(attrs={**_TEXT, "type": "time"}, format="%H:%M"),
    )

    class Meta:
        model = Event
        fields = [
            "form",
            "title",
            "description",
            "location",
            "image",
            "cost",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs=_TEXT),
            "location": forms.TextInput(attrs=_TEXT),
            "image": forms.ClearableFileInput(attrs={"class": "file-input w-full"}),
            "cost": forms.NumberInput(attrs={**_TEXT, "step": "0.01"}),
            "is_published": forms.CheckboxInput(attrs=_CHECKBOX),
        }

    def __init__(self, *args, association=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.association = association
        if association and association.default_location:
            self.fields["location"].initial = association.default_location

        # One open form: assigned automatically, no choice to offer. Several:
        # a select, deliberately last on the page so it stays a detail rather
        # than the first thing an editor has to decide.
        open_forms = list(
            PublicForm.objects.filter(association=association, is_open=True)
        )
        self._auto_form = None
        if len(open_forms) <= 1:
            self._auto_form = open_forms[0] if open_forms else None
            del self.fields["form"]
        else:
            self.fields["form"].queryset = PublicForm.objects.filter(
                pk__in=[form.pk for form in open_forms]
            )
            self.fields["form"].widget.attrs.update({"class": "select w-full"})
            default = next((form for form in open_forms if form.is_default), None)
            if default:
                self.fields["form"].initial = default.pk

    def save(self, commit=True):
        self.instance.association = self.association
        if self._auto_form is not None:
            self.instance.form = self._auto_form
        self.instance.starts_at = timezone.make_aware(
            datetime.combine(
                self.cleaned_data["starts_date"], self.cleaned_data["starts_time"]
            )
        )
        return super().save(commit=commit)
