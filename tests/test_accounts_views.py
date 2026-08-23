import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_account_hub_renders(logged_client):
    response = logged_client.get(reverse("account-hub"))

    assert response.status_code == 200
