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
    list_display = ("name", "city", "membership_fee")
    prepopulated_fields = {"slug": ("name",)}


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
