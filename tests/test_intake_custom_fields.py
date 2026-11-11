import pytest
from django import forms

from intake.custom_fields import (
    build_custom_section_form,
    data_on_file,
    load_initial,
    save_answers,
)
from intake.models import CustomField, Submission

pytestmark = pytest.mark.django_db


@pytest.fixture
def custom_section(public_form):
    return public_form.sections.create(key="orario", title="Orario", is_custom=True)


def test_one_django_field_is_built_per_custom_field(custom_section):
    custom_section.custom_fields.create(label="Preferenza", field_type="text")
    custom_section.custom_fields.create(label="Note", field_type="textarea")

    form_class = build_custom_section_form(custom_section)

    assert len(form_class().fields) == 2


@pytest.mark.parametrize(
    ("field_type", "expected_class"),
    [
        (CustomField.FieldType.TEXT, forms.CharField),
        (CustomField.FieldType.TEXTAREA, forms.CharField),
        (CustomField.FieldType.SELECT, forms.ModelChoiceField),
        (CustomField.FieldType.MULTISELECT, forms.ModelMultipleChoiceField),
        (CustomField.FieldType.CHECKBOX, forms.BooleanField),
        (CustomField.FieldType.NUMBER, forms.DecimalField),
    ],
)
def test_each_field_type_maps_to_its_django_field(
    custom_section, field_type, expected_class
):
    custom_field = custom_section.custom_fields.create(
        label="Domanda", field_type=field_type
    )

    form_class = build_custom_section_form(custom_section)

    field = form_class().fields[f"field_{custom_field.pk}"]
    assert type(field) is expected_class


def test_textarea_uses_a_textarea_widget(custom_section):
    custom_field = custom_section.custom_fields.create(
        label="Note", field_type=CustomField.FieldType.TEXTAREA
    )

    form_class = build_custom_section_form(custom_section)

    field = form_class().fields[f"field_{custom_field.pk}"]
    assert isinstance(field.widget, forms.Textarea)


def test_the_required_flag_is_carried_over(custom_section):
    required = custom_section.custom_fields.create(
        label="Obbligatoria", field_type="text", is_required=True
    )
    optional = custom_section.custom_fields.create(
        label="Facoltativa", field_type="text", is_required=False
    )

    form_class = build_custom_section_form(custom_section)
    fields = form_class().fields

    assert fields[f"field_{required.pk}"].required is True
    assert fields[f"field_{optional.pk}"].required is False


def test_label_and_help_text_are_carried_over(custom_section):
    custom_field = custom_section.custom_fields.create(
        label="Preferenza", help_text="Scegli con calma", field_type="text"
    )

    form_class = build_custom_section_form(custom_section)

    field = form_class().fields[f"field_{custom_field.pk}"]
    assert field.label == "Preferenza"
    assert field.help_text == "Scegli con calma"


def test_a_select_field_offers_its_choices(custom_section):
    custom_field = custom_section.custom_fields.create(
        label="Fascia", field_type=CustomField.FieldType.SELECT
    )
    morning = custom_field.choices.create(label="Mattina", order=0)

    form_class = build_custom_section_form(custom_section)

    field = form_class().fields[f"field_{custom_field.pk}"]
    assert morning in field.queryset


def test_load_initial_is_empty_for_an_unsaved_submission(custom_section):
    custom_section.custom_fields.create(label="Preferenza", field_type="text")

    assert load_initial(custom_section, Submission()) == {}


def test_load_initial_is_empty_for_an_unanswered_submission(custom_section, submission):
    custom_section.custom_fields.create(label="Preferenza", field_type="text")

    assert load_initial(custom_section, submission) == {}


def test_load_initial_returns_the_saved_text(custom_section, submission):
    custom_field = custom_section.custom_fields.create(
        label="Preferenza", field_type="text"
    )
    submission.custom_answers.create(field=custom_field, value_text="Mattina")

    initial = load_initial(custom_section, submission)

    assert initial == {f"field_{custom_field.pk}": "Mattina"}


def test_load_initial_returns_true_for_a_checked_checkbox(custom_section, submission):
    custom_field = custom_section.custom_fields.create(
        label="Accetto", field_type=CustomField.FieldType.CHECKBOX
    )
    submission.custom_answers.create(field=custom_field, value_text="True")

    initial = load_initial(custom_section, submission)

    assert initial == {f"field_{custom_field.pk}": True}


def test_load_initial_returns_the_chosen_option_for_a_select(
    custom_section, submission
):
    custom_field = custom_section.custom_fields.create(
        label="Fascia", field_type=CustomField.FieldType.SELECT
    )
    morning = custom_field.choices.create(label="Mattina")
    answer = submission.custom_answers.create(field=custom_field)
    answer.value_choices.add(morning)

    initial = load_initial(custom_section, submission)

    assert initial == {f"field_{custom_field.pk}": morning.pk}


def test_load_initial_returns_the_chosen_options_for_a_multiselect(
    custom_section, submission
):
    custom_field = custom_section.custom_fields.create(
        label="Interessi", field_type=CustomField.FieldType.MULTISELECT
    )
    morning = custom_field.choices.create(label="Mattina")
    evening = custom_field.choices.create(label="Sera")
    answer = submission.custom_answers.create(field=custom_field)
    answer.value_choices.set([morning, evening])

    initial = load_initial(custom_section, submission)

    assert set(initial[f"field_{custom_field.pk}"]) == {morning, evening}


def test_save_answers_writes_the_text_value(custom_section, submission):
    custom_field = custom_section.custom_fields.create(
        label="Preferenza", field_type="text"
    )

    save_answers(custom_section, submission, {f"field_{custom_field.pk}": "Mattina"})

    answer = submission.custom_answers.get(field=custom_field)
    assert answer.value_text == "Mattina"


def test_save_answers_updates_rather_than_duplicates(custom_section, submission):
    custom_field = custom_section.custom_fields.create(
        label="Preferenza", field_type="text"
    )
    save_answers(custom_section, submission, {f"field_{custom_field.pk}": "Mattina"})

    save_answers(custom_section, submission, {f"field_{custom_field.pk}": "Sera"})

    assert submission.custom_answers.count() == 1
    assert submission.custom_answers.get().value_text == "Sera"


def test_save_answers_sets_the_chosen_option_for_a_select(custom_section, submission):
    custom_field = custom_section.custom_fields.create(
        label="Fascia", field_type=CustomField.FieldType.SELECT
    )
    morning = custom_field.choices.create(label="Mattina")

    save_answers(custom_section, submission, {f"field_{custom_field.pk}": morning})

    answer = submission.custom_answers.get(field=custom_field)
    assert list(answer.value_choices.all()) == [morning]


def test_save_answers_sets_the_chosen_options_for_a_multiselect(
    custom_section, submission
):
    custom_field = custom_section.custom_fields.create(
        label="Interessi", field_type=CustomField.FieldType.MULTISELECT
    )
    morning = custom_field.choices.create(label="Mattina")
    evening = custom_field.choices.create(label="Sera")

    save_answers(
        custom_section,
        submission,
        {f"field_{custom_field.pk}": [morning, evening]},
    )

    answer = submission.custom_answers.get(field=custom_field)
    assert set(answer.value_choices.all()) == {morning, evening}


def test_save_answers_ignores_fields_missing_from_cleaned_data(
    custom_section, submission
):
    custom_section.custom_fields.create(label="Preferenza", field_type="text")

    save_answers(custom_section, submission, {})

    assert not submission.custom_answers.exists()


def test_data_on_file_is_empty_for_an_unanswered_submission(custom_section, submission):
    custom_section.custom_fields.create(label="Preferenza", field_type="text")

    assert data_on_file(custom_section, submission) == {}


def test_data_on_file_passes_on_for_a_checked_checkbox(custom_section, submission):
    custom_field = custom_section.custom_fields.create(
        label="Accetto", field_type=CustomField.FieldType.CHECKBOX
    )
    submission.custom_answers.create(field=custom_field, value_text="True")

    assert data_on_file(custom_section, submission) == {
        f"field_{custom_field.pk}": "on"
    }


def test_data_on_file_omits_an_unchecked_checkbox(custom_section, submission):
    custom_field = custom_section.custom_fields.create(
        label="Accetto", field_type=CustomField.FieldType.CHECKBOX
    )
    submission.custom_answers.create(field=custom_field, value_text="False")

    assert data_on_file(custom_section, submission) == {}


def test_data_on_file_lists_the_chosen_option_pks_for_a_multiselect(
    custom_section, submission
):
    custom_field = custom_section.custom_fields.create(
        label="Interessi", field_type=CustomField.FieldType.MULTISELECT
    )
    morning = custom_field.choices.create(label="Mattina")
    evening = custom_field.choices.create(label="Sera")
    answer = submission.custom_answers.create(field=custom_field)
    answer.value_choices.set([morning, evening])

    data = data_on_file(custom_section, submission)

    assert set(data[f"field_{custom_field.pk}"]) == {morning.pk, evening.pk}


def test_data_on_file_carries_over_a_plain_text_value(custom_section, submission):
    custom_field = custom_section.custom_fields.create(
        label="Preferenza", field_type="text"
    )
    submission.custom_answers.create(field=custom_field, value_text="Mattina")

    assert data_on_file(custom_section, submission) == {
        f"field_{custom_field.pk}": "Mattina"
    }
