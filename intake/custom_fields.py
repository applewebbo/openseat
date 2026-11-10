from django import forms

from intake.forms import apply_daisyui_styles
from intake.models import CustomField


def _field_name(custom_field):
    return f"field_{custom_field.pk}"


def _build_field(custom_field):
    field_type = CustomField.FieldType
    common = {
        "label": custom_field.label,
        "help_text": custom_field.help_text,
        "required": custom_field.is_required,
    }
    if custom_field.field_type == field_type.TEXT:
        return forms.CharField(**common)
    if custom_field.field_type == field_type.TEXTAREA:
        return forms.CharField(widget=forms.Textarea, **common)
    if custom_field.field_type == field_type.SELECT:
        return forms.ModelChoiceField(queryset=custom_field.choices.all(), **common)
    if custom_field.field_type == field_type.MULTISELECT:
        # A plain multi-select, not CheckboxSelectMultiple: the latter's
        # input_type is "checkbox", which the generic section-form template
        # would then render as if it were a single boolean field.
        return forms.ModelMultipleChoiceField(
            queryset=custom_field.choices.all(), widget=forms.SelectMultiple, **common
        )
    if custom_field.field_type == field_type.CHECKBOX:
        return forms.BooleanField(**common)
    return forms.DecimalField(**common)  # NUMBER


class _CustomSectionForm(forms.Form):
    """Base for a custom section's form — fields are added per section."""

    template_name = "intake/forms/section-form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_daisyui_styles(self)


def build_custom_section_form(section):
    """One class per call: its fields come from this section's `CustomField`
    rows — data, not code — so a new question never needs a deploy."""
    fields = {
        _field_name(custom_field): _build_field(custom_field)
        for custom_field in section.custom_fields.all()
    }
    return type("CustomSectionForm", (_CustomSectionForm,), fields)


def load_initial(section, submission):
    """What this submission already answered, keyed like the built form."""
    if submission.pk is None:
        return {}
    answers = {
        answer.field_id: answer
        for answer in submission.custom_answers.filter(
            field__section=section
        ).prefetch_related("value_choices")
    }
    initial = {}
    for custom_field in section.custom_fields.all():
        answer = answers.get(custom_field.pk)
        if answer is None:
            continue
        name = _field_name(custom_field)
        if custom_field.field_type == CustomField.FieldType.MULTISELECT:
            initial[name] = list(answer.value_choices.all())
        elif custom_field.field_type == CustomField.FieldType.SELECT:
            choice = answer.value_choices.first()
            initial[name] = choice.pk if choice else None
        elif custom_field.field_type == CustomField.FieldType.CHECKBOX:
            initial[name] = answer.value_text == "True"
        else:
            initial[name] = answer.value_text
    return initial


def save_answers(section, submission, cleaned_data):
    """Writes one `CustomAnswer` per field this section asked, from cleaned_data."""
    for custom_field in section.custom_fields.all():
        name = _field_name(custom_field)
        if name not in cleaned_data:
            continue
        value = cleaned_data[name]
        answer, _created = submission.custom_answers.get_or_create(field=custom_field)
        if custom_field.field_type == CustomField.FieldType.MULTISELECT:
            answer.value_choices.set(value)
        elif custom_field.field_type == CustomField.FieldType.SELECT:
            answer.value_choices.set([value] if value else [])
        else:
            answer.value_text = "" if value in (None, "") else str(value)
            answer.save(update_fields=["value_text"])
