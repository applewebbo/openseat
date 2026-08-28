from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from intake.models import (
    AgeBracket,
    Association,
    PublicForm,
    Section,
    Submission,
    Subscription,
)


class SectionInline(admin.TabularInline):
    """The catalogue the organiser switches on and off for this form."""

    model = Section
    extra = 0
    fields = ("key", "order", "is_enabled")


class AgeBracketInline(admin.TabularInline):
    model = AgeBracket
    extra = 0
    fields = ("label", "min_age", "max_age", "order")


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    """One installation, one association — so the admin offers exactly one.

    The home page is edited here, and it is the first thing on the form: the
    volunteer who comes to change a paragraph should not have to walk past the
    tax code to find it.
    """

    list_display = ("name", "city", "membership_fee")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AgeBracketInline]
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
            _("Bookings"),
            {"fields": ("booking_close_mode",)},
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
    list_select_related = ("association",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [SectionInline]


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ("signatory_name", "role", "subject", "state", "signed_at", "ip")
    readonly_fields = fields


class FormFilter(admin.SimpleListFilter):
    """The stock FK filter builds its choices with `str(form)` per row, and
    that string pulls in `form.association` — one query per form listed. Only
    matters once a few seasons of forms pile up, but `select_related` here
    keeps that constant instead of linear in form count."""

    title = _("form")
    parameter_name = "form"

    def lookups(self, request, model_admin):
        forms = PublicForm.objects.select_related("association")
        return [(form.pk, str(form)) for form in forms]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(form_id=self.value())
        return queryset


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("member_display", "form", "state", "image_consent", "submitted_at")
    list_filter = ("state", FormFilter, "subject_type")
    search_fields = ("applicant_last_name", "member_last_name", "applicant_email")
    inlines = [SubscriptionInline]

    def get_queryset(self, request):
        # `form` is shown as a column and its `__str__` reads `association`,
        # `image_consent` reads `subscriptions` — without these every row
        # shown would cost one or two extra queries each.
        return (
            super()
            .get_queryset(request)
            .select_related("form__association")
            .prefetch_related("subscriptions")
        )

    @admin.display(description=_("images"), boolean=True)
    def image_consent(self, obj):
        """Whether diffusion is actually allowed, second signature included."""
        return obj.image_consent_active
