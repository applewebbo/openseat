import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_check_is_reachable_without_login(client):
    response = client.get(reverse("health-check"), {"format": "json"})

    assert response.status_code == 200
    assert response.json() == {"Database(alias='default')": "OK"}
