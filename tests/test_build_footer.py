import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_the_home_footer_signs_the_build(client, association):
    content = client.get(reverse("home")).content.decode()

    assert "Webbografico" in content
    assert "v2026.1" in content


def test_the_public_pages_sign_it_too(client, event):
    """Same footer, so a screenshot of any page says which build made it."""
    content = client.get(event.get_absolute_url()).content.decode()

    assert "Webbografico" in content
    assert "v2026.1" in content


def test_the_version_comes_from_the_settings(client, association, settings):
    settings.APP_VERSION = "2027.4.2"

    content = client.get(reverse("home")).content.decode()

    assert "v2027.4.2" in content


def test_the_vendor_links_to_its_own_site(client, association, settings):
    settings.APP_VENDOR_URL = "https://webbografico.example"

    content = client.get(reverse("home")).content.decode()

    assert 'href="https://webbografico.example"' in content


def test_the_version_links_to_the_source(client, association, settings):
    """Self-hosted and open source: the footer says where the code is."""
    settings.APP_SOURCE_URL = "https://github.example/openseat"

    content = client.get(reverse("home")).content.decode()

    assert 'href="https://github.example/openseat"' in content
