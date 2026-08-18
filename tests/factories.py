import factory
from django.contrib.auth import get_user_model

from intake.models import (
    Association,
    PublicForm,
    SectionKey,
    SubjectType,
    Submission,
    Subscription,
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.django.Password("password")


class AssociationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Association
        django_get_or_create = ("slug",)

    name = "L'Ontano - La Ca' di Asu APS"
    slug = factory.Sequence(lambda n: f"associazione-{n}")
    street = "Via Delle Scuole 16"
    postcode = "28100"
    city = "Novara"
    tax_code = "94026180029"
    email = "associazionelontano@gmail.com"
    statute_url = "https://www.lacadiasu.it/chi-siamo/#statuto"
    membership_fee = 10


class PublicFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PublicForm
        django_get_or_create = ("slug",)
        skip_postgeneration_save = True

    association = factory.SubFactory(AssociationFactory)
    slug = factory.Sequence(lambda n: f"adesione-{n}")
    title = "Richiesta di adesione"

    @factory.post_generation
    def sections(obj, create, extracted, **kwargs):
        """Every form ships the whole catalogue; the organiser switches parts off."""
        if create:
            obj.install_sections()


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    form = factory.SubFactory(PublicFormFactory)


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    submission = factory.SubFactory(SubmissionFactory)
    signatory_name = "Maria Rossi"
    role = Subscription.Role.PRIMARY
    subject = Subscription.Subject.MEMBERSHIP
    state = Subscription.State.SIGNED


class MinorSubmissionFactory(SubmissionFactory):
    """A draft filled in as far as the review step, for a minor with two parents."""

    subject_type = SubjectType.MINOR
    applicant_first_name = "Maria"
    applicant_last_name = "Rossi"
    applicant_birth_date = "1985-04-12"
    applicant_birth_place = "Novara"
    applicant_tax_code = "RSSMRA85D52F952F"
    applicant_street = "Via Roma 4"
    applicant_number = "4"
    applicant_postcode = "28100"
    applicant_city = "Novara"
    applicant_phone = "3401234567"
    applicant_email = "maria.rossi@example.com"
    member_first_name = "Luca"
    member_last_name = "Rossi"
    member_birth_date = "2015-09-03"
    member_birth_place = "Novara"
    member_tax_code = "RSSLCU15P03F952V"
    member_street = "Via Roma 4"
    member_number = "4"
    member_city = "Novara"
    accepts_statute = True
    sole_holder = False
    second_parent_first_name = "Paolo"
    second_parent_last_name = "Rossi"
    second_parent_email = "paolo.rossi@example.com"
    consent_images = True
    consent_whatsapp = False
    place = "Novara"


__all__ = [
    "AssociationFactory",
    "MinorSubmissionFactory",
    "PublicFormFactory",
    "SectionKey",
    "SubmissionFactory",
    "SubscriptionFactory",
    "UserFactory",
]
