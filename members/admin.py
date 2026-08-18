from datetime import date

from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from members.export import write_csv
from members.models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
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
    actions = ["export_selected", "mark_ratified"]

    @admin.action(description=_("Export the selected members to CSV"))
    def export_selected(self, request, queryset):
        """Filter the list by joining date first, then select all and export."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="soci-{date.today().isoformat()}.csv"'
        )
        write_csv(response, queryset)
        return response

    @admin.action(description=_("Record the board's ratification today"))
    def mark_ratified(self, request, queryset):
        updated = queryset.filter(ratified_on__isnull=True).update(
            ratified_on=date.today()
        )
        self.message_user(
            request, _("%(count)d admissions minuted.") % {"count": updated}
        )
