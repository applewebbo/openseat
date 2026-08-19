import pytest
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestBranding:
    def test_the_association_names_the_admin(self, staff_client, association):
        content = staff_client.get(reverse("admin:index")).content.decode()

        assert "Ontano" in content

    def test_the_logo_replaces_the_name_when_there_is_one(
        self, staff_client, association
    ):
        association.logo = "associations/ontano.png"
        association.save()

        content = staff_client.get(reverse("admin:index")).content.decode()

        assert association.logo.url in content

    def test_a_fresh_install_falls_back_to_the_product_name(self, staff_client):
        content = staff_client.get(reverse("admin:index")).content.decode()

        assert "OpenSeat" in content

    def test_the_login_page_carries_the_branding_too(self, client, association):
        """It is the first page a volunteer sees, and the only public one."""
        content = client.get(reverse("admin:login")).content.decode()

        assert "Ontano" in content

    def test_the_palette_is_linked(self, staff_client, association):
        content = staff_client.get(reverse("admin:index")).content.decode()

        assert reverse("theme-css-current") in content


class TestAppOrder:
    def test_the_daily_work_comes_before_the_plumbing(self, staff_client, association):
        response = staff_client.get(reverse("admin:index"))

        labels = [app["app_label"] for app in response.context["app_list"]]

        assert labels.index("events") < labels.index("members")
        assert labels.index("members") < labels.index("intake")
        assert labels.index("intake") < labels.index("accounts")

    def test_an_app_nobody_decided_about_is_kept_last(
        self, staff_client, association
    ):
        response = staff_client.get(reverse("admin:index"))

        labels = [app["app_label"] for app in response.context["app_list"]]

        assert labels[-1] not in {"events", "members", "intake", "accounts"}

    def test_an_editor_only_sees_what_they_may_touch(self, client, user):
        from accounts.groups import ensure_editor_group

        user.is_staff = True
        user.save()
        user.groups.add(ensure_editor_group())
        client.force_login(user)

        response = client.get(reverse("admin:index"))

        assert [app["app_label"] for app in response.context["app_list"]] == ["events"]


def test_the_project_site_is_the_one_in_use():
    from core.admin import OpenSeatAdminSite

    assert isinstance(admin.site, OpenSeatAdminSite)
