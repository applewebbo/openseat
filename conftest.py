import pytest
from django.utils.translation import override
from pytest_factoryboy import register

from tests.factories import (
    AdultSubmissionFactory,
    AssociationFactory,
    BookingFactory,
    EventFactory,
    MemberFactory,
    MinorSubmissionFactory,
    PublicFormFactory,
    SubmissionFactory,
    SubscriptionFactory,
    UserFactory,
)

# Registered as "user" rather than the model-derived "custom_user" default.
register(UserFactory, "user")
register(AssociationFactory, "association")
register(PublicFormFactory, "public_form")
register(SubmissionFactory, "submission")
register(SubscriptionFactory, "subscription")
register(MinorSubmissionFactory, "minor_submission")
register(AdultSubmissionFactory, "adult_submission")
register(MemberFactory, "member")
register(EventFactory, "event")
register(BookingFactory, "booking")


@pytest.fixture
def logged_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def english():
    """Assert on error text in the source language, not the active locale."""
    with override("en"):
        yield


@pytest.fixture
def staff_client(client, user):
    """The organiser's own view of the app: everything behind the admin."""
    user.is_staff = user.is_superuser = True
    user.save()
    client.force_login(user)
    return client
