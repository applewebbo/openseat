from datetime import date

from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportActionModelAdmin
from import_export.formats.base_formats import CSV, XLSX
from import_export.forms import ConfirmImportForm, ImportForm

from members.models import Member
from members.resources import MemberResource


class MemberImportForm(ImportForm):
    mode = forms.ChoiceField(
        label=_("If the tax code already exists on the register"),
        choices=[
            ("overwrite", _("Overwrite the existing member")),
            ("append", _("Always add as a new member")),
        ],
        initial="overwrite",
    )


class MemberConfirmImportForm(ConfirmImportForm):
    mode = forms.CharField(widget=forms.HiddenInput())


@admin.register(Member)
class MemberAdmin(ImportExportActionModelAdmin):
    resource_classes = [MemberResource]
    import_form_class = MemberImportForm
    confirm_form_class = MemberConfirmImportForm
    import_formats = [CSV, XLSX]
    export_formats = [CSV, XLSX]

    list_display = (
        "last_name",
        "first_name",
        "contact_email",
        "joined_on",
        "ratified_on",
        "is_active",
    )
    list_filter = ("association", "is_active", "joined_on", "ratified_on")
    search_fields = ("last_name", "first_name", "tax_code", "contact_email")
    # Needed by the booking inline in events, which picks members by name.
    date_hierarchy = "joined_on"
    readonly_fields = ("submission", "joined_on")
    actions = ["mark_ratified"]

    def get_confirm_form_initial(self, request, import_form):
        initial = super().get_confirm_form_initial(request, import_form)
        if import_form is not None:
            initial["mode"] = import_form.cleaned_data["mode"]
        return initial

    def get_import_resource_kwargs(self, request, **kwargs):
        resource_kwargs = super().get_import_resource_kwargs(request, **kwargs)
        form = kwargs.get("form")
        if (
            form is not None
            and hasattr(form, "cleaned_data")
            and "mode" in form.cleaned_data
        ):
            resource_kwargs["mode"] = form.cleaned_data["mode"]
        return resource_kwargs

    @admin.action(description=_("Record the board's ratification today"))
    def mark_ratified(self, request, queryset):
        updated = queryset.filter(ratified_on__isnull=True).update(
            ratified_on=date.today()
        )
        self.message_user(
            request, _("%(count)d admissions minuted.") % {"count": updated}
        )
