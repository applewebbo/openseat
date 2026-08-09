import pytest
from django.utils.translation import override
from pytest_factoryboy import register

from tests.factories import UserFactory

# Registered as "user" rather than the model-derived "custom_user" default.
register(UserFactory, "user")


@pytest.fixture
def logged_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def english():
    """Assert on error text in the source language, not the active locale."""
    with override("en"):
        yield
