import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    """A media root of our own, so a run never litters the real one with files."""
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


def test_a_fresh_install_has_no_info_page(client):
    response = client.get(reverse("info"))

    assert response.status_code == 404


def test_an_unpublished_page_is_a_404(client, association):
    response = client.get(reverse("info"))

    assert response.status_code == 404


def test_a_published_page_shows_the_contact_details(client, association):
    association.info_is_published = True
    association.save()

    response = client.get(reverse("info"))

    assert response.status_code == 200
    content = response.content.decode()
    assert association.street in content
    assert association.tax_code in content


def test_the_info_page_carries_the_shared_footer(client, association):
    association.info_is_published = True
    association.save()

    content = client.get(reverse("info")).content.decode()

    assert "Contact us" in content or "Contattaci" in content


def test_a_script_in_the_info_content_never_reaches_the_page(client, association):
    association.info_is_published = True
    association.info_content = "<p>Ciao</p><script>alert(1)</script>"
    association.save()

    response = client.get(reverse("info"))

    assert b"<script>" not in response.content


def test_the_statute_link_points_to_the_uploaded_file_when_there_is_one(
    client, association
):
    association.info_is_published = True
    association.statute_file.save(
        "statuto.pdf", ContentFile(b"%PDF-1.4 fake"), save=False
    )
    association.save()

    response = client.get(reverse("info"))

    assert association.statute_file.url.encode() in response.content
    assert association.statute_url.encode() not in response.content
    assert "Scarica lo statuto" in response.content.decode()


def test_the_statute_link_falls_back_to_the_url_without_a_file(client, association):
    association.info_is_published = True
    association.save()

    response = client.get(reverse("info"))

    assert association.statute_url.encode() in response.content
    assert "Leggi lo statuto" in response.content.decode()
    assert "Scarica lo statuto" not in response.content.decode()


def test_no_statute_link_when_neither_is_set(client, association):
    association.info_is_published = True
    association.statute_url = ""
    association.save()

    response = client.get(reverse("info"))

    assert "Scarica lo statuto" not in response.content.decode()
    assert "Leggi lo statuto" not in response.content.decode()


def test_the_home_page_links_to_a_published_info_page(client, association):
    association.info_is_published = True
    association.save()

    response = client.get(reverse("home"))

    assert reverse("info").encode() in response.content


def test_the_home_page_falls_back_to_the_statute_link_when_unpublished(
    client, association
):
    response = client.get(reverse("home"))

    assert association.statute_url.encode() in response.content
    assert reverse("info").encode() not in response.content


def test_the_home_page_falls_back_to_the_statute_file_when_unpublished(
    client, association
):
    association.statute_file.save(
        "statuto.pdf", ContentFile(b"%PDF-1.4 fake"), save=False
    )
    association.statute_url = ""
    association.save()

    response = client.get(reverse("home"))

    assert association.statute_file.url.encode() in response.content
