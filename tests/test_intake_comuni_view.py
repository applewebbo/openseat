import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_it_returns_the_comuni_for_the_chosen_province(client):
    response = client.get(reverse("intake:comuni-options"), {"applicant_province": "NO"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Novara" in content
    assert "Milano" not in content


@pytest.mark.django_db
def test_it_reads_a_member_province_field_just_as_well(client):
    response = client.get(reverse("intake:comuni-options"), {"member_province": "NO"})

    assert "Novara" in response.content.decode()


@pytest.mark.django_db
def test_with_no_province_it_offers_no_comuni(client):
    response = client.get(reverse("intake:comuni-options"))

    assert response.content.decode().strip() == "<option value=\"\">—</option>"
