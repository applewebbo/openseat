"""Widget styling shared by forms outside intake, which owns its own copy."""

from django import forms


class DaisyWidgetsMixin:
    """daisyUI classes belong to the form, not to every template rendering it."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault(
                    "class",
                    "checkbox checkbox-primary mt-0.5 [--radius-selector:0.25rem]",
                )
            elif isinstance(widget, forms.RadioSelect):
                widget.attrs.setdefault("class", "radio radio-primary mt-0.5")
            else:
                widget.attrs.setdefault("class", "input input-bordered w-full")
