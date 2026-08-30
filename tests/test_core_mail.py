import pytest

from core.mail import from_header

pytestmark = pytest.mark.django_db


def test_the_from_header_names_the_association(association, settings):
    settings.DEFAULT_FROM_EMAIL = "noreply@example.com"
    association.name = "Circolo Aurora"

    assert from_header(association) == "Circolo Aurora <noreply@example.com>"
