from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from intake.models import (
    AgeBracket,
    Association,
    CustomField,
    CustomFieldChoice,
    PublicForm,
    Section,
    SectionKey,
    Submission,
    Subscription,
)


class SectionInline(admin.TabularInline):
    """The catalogue the organiser switches on and off for this form.

    A new row is added from `SectionAdmin`, not here: that is where a blank
    key turns into a generated slug and `is_custom` is set.
    """

    model = Section
    extra = 0
    fields = ("key", "title", "order", "is_enabled")
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


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
            {"fields": ("street", "postcode", "city", "tax_code", "email")},
        ),
        (
            _("Statute and fee"),
            {"fields": ("statute_file", "statute_url", "membership_fee")},
        ),
        (
            _("Info page"),
            {
                "fields": ("info_is_published", "info_content"),
                "description": _(
                    "A separate page with the address, tax code, email and "
                    "statute link above, plus this optional text. Publishing "
                    "it also links it from the home page."
                ),
            },
        ),
        (
            _("Social links"),
            {
                "fields": ("website_url", "facebook_url", "instagram_url"),
                "description": _(
                    "Shown as icons in the home page footer when filled in."
                ),
            },
        ),
        (
            _("Bookings"),
            {"fields": ("booking_close_mode", "default_location")},
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
    list_display = ("title", "association", "is_open", "is_default", "created_at")
    list_filter = ("is_open", "is_default", "association")
    list_select_related = ("association",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [SectionInline]


class CustomFieldInline(admin.TabularInline):
    """Quick listing and ordering; a field's own choices live on its own page."""

    model = CustomField
    extra = 0
    fields = ("label", "field_type", "help_text", "is_required", "order")
    show_change_link = True


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    """One page per section: a fixed one only has its text to edit here, a
    custom one also gets its questions, linked on to `CustomFieldAdmin`."""

    list_display = ("__str__", "form", "is_custom", "is_enabled", "order")
    list_filter = ("is_custom", "is_enabled", "form")
    list_select_related = ("form",)

    def get_fields(self, request, obj=None):
        # A blank add form only needs what every section has; the rest
        # (statute/privacy text, consent labels) belongs to one specific
        # fixed section each and would otherwise sit there unexplained.
        fields = ["form"]
        if obj is not None:
            fields.append("key")
        fields.append("title")
        if obj is not None and obj.key in (SectionKey.STATUTE, SectionKey.PRIVACY):
            fields.append("custom_body")
        if obj is not None and obj.key == SectionKey.CONSENTS:
            fields += ["consent_images_label", "consent_whatsapp_label"]
        fields += ["order", "is_enabled"]
        return fields

    def get_readonly_fields(self, request, obj=None):
        # Blank on a new section: `Section.save()` generates it from the
        # title. A fixed section's key is what the wizard matches on, so it
        # is never the organiser's to change either.
        return ("key",) if obj is not None else ()

    def get_inlines(self, request, obj):
        if obj is not None and obj.is_custom:
            return [CustomFieldInline]
        return []


class CustomFieldChoiceInline(admin.TabularInline):
    model = CustomFieldChoice
    extra = 0
    fields = ("label", "order")


@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ("label", "section", "field_type", "is_required", "order")
    list_filter = ("field_type", "section__form")
    list_select_related = ("section",)

    def get_inlines(self, request, obj):
        if obj is not None and obj.field_type in (
            CustomField.FieldType.SELECT,
            CustomField.FieldType.MULTISELECT,
        ):
            return [CustomFieldChoiceInline]
        return []


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
