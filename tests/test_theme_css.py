import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestThemeStylesheet:
    def test_it_serves_the_association_colours_as_css(self, client, association):
        association.colour_primary = "#112233"
        association.save()

        response = client.get(reverse("theme-css", kwargs={"slug": association.slug}))

        assert response.status_code == 200
        assert response["Content-Type"] == "text/css"
        assert "--assoc-bright: #112233;" in response.content.decode()

    def test_a_colour_that_is_not_a_hex_value_never_reaches_the_stylesheet(
        self, client, association
    ):
        """The field validator runs on forms; a value written straight to the
        database would otherwise be free text inside a stylesheet."""
        type(association).objects.filter(pk=association.pk).update(
            colour_primary="red; } body { display: none"
        )

        content = client.get(
            reverse("theme-css", kwargs={"slug": association.slug})
        ).content.decode()

        assert "display: none" not in content
        assert "--assoc-bright: #ED5C08;" in content

    def test_an_unknown_slug_still_serves_a_usable_palette(self, client):
        content = client.get(
            reverse("theme-css", kwargs={"slug": "nessuna"})
        ).content.decode()

        assert "--assoc-bright: #ED5C08;" in content

    def test_the_admin_gets_the_palette_without_naming_an_association(
        self, client, association
    ):
        """The admin is not under an association's URL, so it asks for the
        installation's own."""
        association.colour_primary = "#112233"
        association.save()

        content = client.get(reverse("theme-css-current")).content.decode()

        assert "--assoc-bright: #112233;" in content

    def test_a_fresh_install_still_gets_a_palette(self, client):
        content = client.get(reverse("theme-css-current")).content.decode()

        assert "--assoc-bright: #ED5C08;" in content

    def test_it_is_public(self, client, association):
        """It is linked from pages people reach without an account."""
        response = client.get(reverse("theme-css", kwargs={"slug": association.slug}))

        assert response.status_code == 200
        assert "max-age=300" in response["Cache-Control"]
