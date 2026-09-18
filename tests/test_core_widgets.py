from datetime import date

from django import forms

from core.widgets import MaskedDateInput


class _DateForm(forms.Form):
    when = forms.DateField(
        label="When", input_formats=["%d/%m/%Y"], widget=MaskedDateInput()
    )


def test_the_widget_renders_the_date_formatted_ddmmyyyy():
    html = _DateForm(initial={"when": date(2015, 9, 3)}).as_p()

    assert 'value="03/09/2015"' in html
    assert 'placeholder="--/--/----"' in html
    assert 'inputmode="numeric"' in html


def test_the_widget_offers_a_calendar_fallback():
    html = _DateForm().as_p()

    assert 'type="date"' in html
    assert "showPicker" not in html  # lives in main.js, not inlined per field


def test_a_valid_date_is_accepted():
    form = _DateForm(data={"when": "03/09/2015"})

    assert form.is_valid()
    assert form.cleaned_data["when"] == date(2015, 9, 3)


def test_a_calendar_impossible_date_is_refused():
    form = _DateForm(data={"when": "31/04/2020"})

    assert not form.is_valid()
    assert "when" in form.errors


def test_the_old_iso_format_is_no_longer_accepted():
    """The mask only ever produces dd/mm/yyyy, so nothing else should parse —
    an iso value slipping through would mean the field silently accepts input
    the widget itself could never have typed."""
    form = _DateForm(data={"when": "2015-09-03"})

    assert not form.is_valid()
