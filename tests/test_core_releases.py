import pytest
from django.urls import reverse

from core.releases import RELEASES


@pytest.mark.django_db
class TestReleasesPage:
    def test_page_renders(self, client):
        response = client.get(reverse("releases"))

        assert response.status_code == 200
        assert "pages/releases.html" in [t.name for t in response.templates]

    def test_context_carries_the_release_list(self, client):
        response = client.get(reverse("releases"))

        assert response.context["releases"] == RELEASES

    def test_an_anonymous_visitor_can_reach_it(self, client):
        response = client.get(reverse("releases"))

        assert response.status_code == 200


class TestReleasesData:
    def test_every_entry_is_well_formed(self):
        for entry in RELEASES:
            assert entry["version"]
            assert not entry["version"].startswith("v")
            assert 2 <= len(entry["notes"]) <= 4
            assert all(note.strip() for note in entry["notes"])
