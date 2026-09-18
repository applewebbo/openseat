from django import forms


class MaskedDateInput(forms.DateInput):
    """A typeable dd/mm/yyyy field, with the native picker as a fallback.

    Replaces the bare `type="date"` input: on mobile Safari it opens a
    wheel/calendar picker, which makes reaching a birth date decades back a
    long scroll. Typing is the primary path here — the calendar button next
    to the field still opens the native picker for anyone who prefers to
    browse, synced back into the same text value.
    """

    template_name = "widgets/masked-date-input.html"

    def __init__(self, attrs=None):
        default_attrs = {"class": "input input-bordered w-full pr-10"}
        super().__init__(attrs={**default_attrs, **(attrs or {})}, format="%d/%m/%Y")
