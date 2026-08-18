import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from intake.models import Association


def past(days):
    return timezone.now() - datetime.timedelta(days=days)


def future(days):
    return timezone.now() + datetime.timedelta(days=days)


@pytest.mark.django_db
class TestAssociationContent:
    def test_home_shows_the_association_name_and_title(self, client, association):
        association.home_title = "Un branco di asini e un modo diverso di stare insieme"
        association.save()

        content = client.get(reverse("home")).content.decode()

        # The apostrophe in the name arrives escaped, as it should.
        assert "Ontano" in content
        assert "Un branco di asini" in content

    def test_the_description_keeps_its_formatting(self, client, association):
        association.home_description = "<p>Ospitiamo <strong>asini</strong>.</p>"
        association.save()

        content = client.get(reverse("home")).content.decode()

        assert "<strong>asini</strong>" in content

    def test_a_script_in_the_description_never_reaches_the_page(
        self, client, association
    ):
        """The description is rendered unescaped, so it is cleaned on the way in."""
        association.home_description = "<p>Ciao</p><script>alert(1)</script>"
        association.save()

        association.refresh_from_db()
        assert "<script>" not in association.home_description
        assert "<p>Ciao</p>" in association.home_description
        assert b"<script>alert(1)</script>" not in client.get(reverse("home")).content

    def test_an_unstyled_link_is_kept_but_defanged(self, association):
        association.home_description = (
            '<p><a href="https://example.org" onclick="x()">qui</a></p>'
        )
        association.save()

        association.refresh_from_db()
        assert 'href="https://example.org"' in association.home_description
        assert "onclick" not in association.home_description


@pytest.mark.django_db
class TestEventSections:
    def test_the_next_event_is_the_featured_one(
        self, client, association, event_factory
    ):
        event_factory(
            association=association, title="Fra un mese", starts_at=future(30)
        )
        soonest = event_factory(
            association=association, title="Domani", starts_at=future(1)
        )

        response = client.get(reverse("home"))

        assert response.context["featured"] == soonest
        assert list(response.context["upcoming"]) == [
            Event.objects.get(title="Fra un mese")
        ]

    def test_past_events_are_listed_newest_first(
        self, client, association, event_factory
    ):
        older = event_factory(association=association, starts_at=past(60))
        newer = event_factory(association=association, starts_at=past(2))

        response = client.get(reverse("home"))

        assert list(response.context["past"]) == [newer, older]
        assert response.context["featured"] is None

    def test_the_featured_event_links_to_its_booking_page(
        self, client, association, event
    ):
        content = client.get(reverse("home")).content.decode()

        assert reverse("events:landing", kwargs={"slug": event.slug}) in content

    def test_an_empty_section_is_not_drawn(self, client, association, event):
        """One event only: neither the 'other dates' list nor the archive shows."""
        content = client.get(reverse("home")).content.decode()

        assert 'id="prossime"' not in content
        assert 'id="archivio"' not in content

    def test_unpublished_events_are_invisible(self, client, association, event_factory):
        event_factory(association=association, is_published=False, starts_at=future(3))

        response = client.get(reverse("home"))

        assert response.context["featured"] is None

    def test_a_second_association_never_takes_over_the_page(
        self, client, association, association_factory, event_factory
    ):
        """The admin forbids a second one; if code makes one anyway, it is ignored.

        Alphabetically "Altra APS" sorts first, which is exactly the trap.
        """
        other = association_factory(slug="altra", name="Altra APS")
        event_factory(association=other, starts_at=future(3))

        response = client.get(reverse("home"))

        assert response.context["association"] == association
        assert response.context["featured"] is None


@pytest.mark.django_db
def test_a_fresh_install_says_what_to_do_next(client):
    assert not Association.objects.exists()

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert response.context["association"] is None
    assert reverse("admin:index").encode() in response.content
