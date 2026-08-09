import pytest
from pytest_factoryboy import register

from tests.factories import UserFactory

# Registered as "user" rather than the model-derived "custom_user" default.
register(UserFactory, "user")


@pytest.fixture
def logged_client(client, user):
    client.force_login(user)
    return client
