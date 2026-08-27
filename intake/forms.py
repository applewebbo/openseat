from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from intake.geo import comune_choices, province_choices
from intake.models import SubjectType, Submission
from intake.validators import (
    validate_phone,
    validate_postcode,
    validate_tax_code,
)

# A consent is a question with two answers, and neither is the default. A single
# checkbox would make silence mean "no" and a pre-tick would make it mean "yes";
# the paper form asks for an explicit mark either way, and so does this.
CONSENT_CHOICES = [("True", _("I give my consent")), ("False", _("I do not consent"))]

HOLDER_CHOICES = [
    (
        "False",
        _(
            "I sign on behalf of the other parent too, in agreement with them "
            "(artt. 316 and 337-ter of the Civil Code)"
        ),
    ),
    ("True", _("I am the sole holder of parental responsibility")),
]


def yes_no_field(label, choices=CONSENT_CHOICES, help_text=""):
    """A required, never pre-selected, two-way answer."""
    return forms.TypedChoiceField(
        label=label,
        help_text=help_text,
        choices=choices,
        coerce=lambda value: value == "True",
        widget=forms.RadioSelect,
        required=True,
        empty_value=None,
    )


class SectionForm(forms.ModelForm):
    """Base for every step: the form owns how it renders, classes included."""

    template_name = "intake/forms/section-form.html"

    class Meta:
        model = Submission
        fields: list[str] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_widgets()

    def style_widgets(self):
        """daisyUI classes belong to the form, not to every template using it."""
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault(
                    "class",
                    "checkbox checkbox-primary mt-0.5 [--radius-selector:0.25rem]",
                )
            elif isinstance(widget, forms.RadioSelect):
                widget.attrs.setdefault("class", "radio radio-primary mt-0.5")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "select w-full")
            else:
                widget.attrs.setdefault("class", "input input-bordered w-full")


class SubjectTypeForm(SectionForm):
    class Meta(SectionForm.Meta):
        fields = ["subject_type"]
        widgets = {"subject_type": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["subject_type"]
        field.required = True
        # A model field with blank=True hands the form an empty first choice,
        # which would render as a fourth, pre-selected answer.
        field.choices = SubjectType.choices
        # The page heading asks the question; a legend would repeat it.
        field.label = ""


class PersonForm(SectionForm):
    """Shared field wiring and layout for the two anagraphic sections."""

    template_name = "intake/forms/person-form.html"
    # Fields grouped into rows of a six-column grid: a house number does not
    # deserve the width of a street name.
    ROWS: list[list[tuple[str, str]]] = []

    def rows(self):
        return [
            [{"field": self[name], "css": css} for name, css in row]
            for row in self.ROWS
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name.endswith("_tax_code"):
                field.validators.append(validate_tax_code)
                field.widget.attrs["autocapitalize"] = "characters"
            if name.endswith("_postcode"):
                field.validators.append(validate_postcode)
                field.widget.attrs["inputmode"] = "numeric"
            if name.endswith("_phone"):
                field.validators.append(validate_phone)
                field.widget.attrs["inputmode"] = "tel"
            if name.endswith("_email"):
                field.widget.attrs["inputmode"] = "email"
            if name.endswith("_birth_date"):
                field.widget = forms.DateInput(
                    attrs={"type": "date", "class": "input input-bordered w-full"},
                    format="%Y-%m-%d",
                )
            if name.endswith("_province"):
                self.fields[name] = forms.ChoiceField(
                    label=field.label,
                    choices=[("", "—")] + province_choices(),
                )
            if name.endswith("_city"):
                # The comuni list depends on the province chosen alongside it,
                # so it is rebuilt here rather than declared as a class
                # attribute — an htmx request swaps it in again when the
                # province select changes.
                prefix = name.removesuffix("_city")
                province_value = self.data.get(f"{prefix}_province") or getattr(
                    self.instance, f"{prefix}_province", ""
                )
                self.fields[name] = forms.ChoiceField(
                    label=field.label,
                    choices=[("", "—")] + comune_choices(province_value),
                    widget=forms.Select(
                        attrs={
                            "hx-get": reverse("intake:comuni-options"),
                            "hx-trigger": f"change from:#id_{prefix}_province",
                            "hx-include": f"#id_{prefix}_province",
                            "hx-target": "this",
                            "hx-swap": "innerHTML",
                        }
                    ),
                )
        for field in self.fields.values():
            field.required = True
        # The province/city fields above are built fresh, after style_widgets()
        # already ran once in SectionForm.__init__ — so they missed it.
        self.style_widgets()

    def clean(self):
        cleaned = super().clean()
        for name, value in cleaned.items():
            if name.endswith("_tax_code") and value:
                cleaned[name] = value.upper()
        return cleaned


class ApplicantForm(PersonForm):
    ROWS = [
        [
            ("applicant_first_name", "sm:col-span-3"),
            ("applicant_last_name", "sm:col-span-3"),
        ],
        [
            ("applicant_birth_date", "sm:col-span-3"),
            ("applicant_birth_place", "sm:col-span-3"),
        ],
        [("applicant_tax_code", "sm:col-span-6")],
        [("applicant_street", "sm:col-span-4"), ("applicant_number", "sm:col-span-2")],
        [
            ("applicant_postcode", "sm:col-span-2"),
            ("applicant_province", "sm:col-span-2"),
            ("applicant_city", "sm:col-span-2"),
        ],
        [("applicant_phone", "sm:col-span-3"), ("applicant_email", "sm:col-span-3")],
    ]

    class Meta(SectionForm.Meta):
        fields = [
            "applicant_first_name",
            "applicant_last_name",
            "applicant_birth_date",
            "applicant_birth_place",
            "applicant_tax_code",
            "applicant_street",
            "applicant_number",
            "applicant_postcode",
            "applicant_province",
            "applicant_city",
            "applicant_phone",
            "applicant_email",
        ]


class MemberForm(PersonForm):
    ROWS = [
        [("member_first_name", "sm:col-span-3"), ("member_last_name", "sm:col-span-3")],
        [
            ("member_birth_date", "sm:col-span-3"),
            ("member_birth_place", "sm:col-span-3"),
        ],
        [("member_tax_code", "sm:col-span-6")],
        [("member_street", "sm:col-span-4"), ("member_number", "sm:col-span-2")],
        [
            ("member_province", "sm:col-span-2"),
            ("member_city", "sm:col-span-4"),
        ],
    ]

    class Meta(SectionForm.Meta):
        fields = [
            "member_first_name",
            "member_last_name",
            "member_birth_date",
            "member_birth_place",
            "member_tax_code",
            "member_street",
            "member_number",
            "member_province",
            "member_city",
        ]


class StatuteForm(SectionForm):
    """Statute, fee, and — when someone signs for another — who holds responsibility.

    The declaration lives here, before the consents section, because it decides
    whether image diffusion needs a second signature at all.
    """

    template_name = "intake/forms/statute-form.html"

    accepts_statute = forms.BooleanField(
        required=True,
        label=_("I accept the statute and undertake to pay the annual membership fee"),
    )
    sole_holder = yes_no_field(
        label=_("Parental responsibility"),
        choices=HOLDER_CHOICES,
        help_text=_(
            "Being separated or divorced does not make you the sole holder: under "
            "shared custody both parents remain holders. You are the sole holder "
            "with exclusive custody, after the other parent's death, or when you "
            "are the only parent who recognised the child."
        ),
    )

    class Meta(SectionForm.Meta):
        fields = [
            "accepts_statute",
            "sole_holder",
            "second_parent_first_name",
            "second_parent_last_name",
            "second_parent_email",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.applies_for_someone_else:
            for name in list(self.fields):
                if name != "accepts_statute":
                    del self.fields[name]
            return
        self.fields["second_parent_first_name"].label = _("Their first name")
        self.fields["second_parent_last_name"].label = _("Their last name")
        self.fields["second_parent_email"].label = _("Their email address")
        self.fields["second_parent_email"].help_text = _(
            "Used only to ask them about the image consents."
        )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("sole_holder") is False:
            for name in (
                "second_parent_first_name",
                "second_parent_last_name",
                "second_parent_email",
            ):
                if not cleaned.get(name):
                    self.add_error(name, _("This field is required."))
        return cleaned


class PrivacyNoticeForm(SectionForm):
    """The notice is read, not filled in; the step still needs a form to advance."""


class ConsentsForm(SectionForm):
    consent_images = yes_no_field(
        label=_("Publishing images on the association's website and social channels")
    )
    consent_whatsapp = yes_no_field(
        label=_("Sending photos and videos through the WhatsApp broadcast list")
    )

    class Meta(SectionForm.Meta):
        fields = ["consent_images", "consent_whatsapp"]


class ReviewForm(SectionForm):
    declaration = forms.BooleanField(
        required=True,
        label=_(
            "I declare that the information above is true and I ask to be "
            "admitted as a member"
        ),
    )

    class Meta(SectionForm.Meta):
        fields = ["place"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["place"].required = True
        self.fields["place"].initial = self.instance.applicant_city


class ResumeLinkForm(forms.Form):
    """Where to send the way back into a draft."""

    template_name = "intake/forms/section-form.html"

    email = forms.EmailField(
        label=_("Email address"),
        help_text=_("We send the link to come back to, and nothing else."),
        widget=forms.EmailInput(
            attrs={"class": "input input-bordered w-full", "inputmode": "email"}
        ),
    )
