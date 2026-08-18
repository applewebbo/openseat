from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from intake.models import Association, PublicForm, Section, Submission, Subscription


class SectionInline(admin.TabularInline):
    """The catalogue the organiser switches on and off for this form."""

    model = Section
    extra = 0
    fields = ("key", "order", "is_enabled")


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    """One installation, one association — so the admin offers exactly one.

    The home page is edited here, and it is the first thing on the form: the
    volunteer who comes to change a paragraph should not have to walk past the
    tax code to find it.
    """

    list_display = ("name", "city", "membership_fee")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = [
        (
            _("Home page"),
            {
                "fields": ("logo", "name", "home_title", "home_description"),
                "description": _(
                    "These four are the public home page, in the order they appear on it."
                ),
            },
        ),
        (
            _("Registered details"),
            {"fields": ("slug", "street", "postcode", "city", "tax_code", "email")},
        ),
        (
            _("Statute and fee"),
            {"fields": ("statute_url", "membership_fee")},
        ),
        (
            _("Colours"),
            {
                "classes": ["collapse"],
                "fields": ("colour_primary", "colour_accent", "colour_neutral"),
                "description": _(
                    "Used across the public pages. Six-digit hex, e.g. #ED5C08."
                ),
            },
        ),
    ]

    def has_add_permission(self, request):
        # A second association would silently split events, members and the
        # home page between two records that look alike.
        return not Association.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PublicForm)
class PublicFormAdmin(admin.ModelAdmin):
    list_display = ("title", "association", "is_open", "created_at")
    list_filter = ("is_open", "association")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [SectionInline]


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ("signatory_name", "role", "subject", "state", "signed_at", "ip")
    readonly_fields = fields


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("member_display", "form", "state", "image_consent", "submitted_at")
    list_filter = ("state", "form", "subject_type")
    search_fields = ("applicant_last_name", "member_last_name", "applicant_email")
    inlines = [SubscriptionInline]

    @admin.display(description=_("images"), boolean=True)
    def image_consent(self, obj):
        """Whether diffusion is actually allowed, second signature included."""
        return obj.image_consent_active
