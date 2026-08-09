import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_renders(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b"OpenSeat" in response.content


@pytest.mark.django_db
def test_home_is_reachable_while_logged_in(logged_client):
    assert logged_client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_admin_requires_authentication(client):
    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
