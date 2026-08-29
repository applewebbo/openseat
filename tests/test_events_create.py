from datetime import date

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from events.models import Event

pytestmark = pytest.mark.django_db


def _post_data(**overrides):
    data = {
        "title": "Una giornata con gli asini",
        "description": "",
        "location": "Ca' di Asu, Olengo",
        "starts_date": "2027-04-20",
        "starts_time": "16:00",
        "cost": "",
        "is_published": "on",
    }
    data.update(overrides)
    return data


def test_an_anonymous_visitor_is_redirected_to_login(client):
    response = client.get(reverse("events:create"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("account_login"))


def test_a_visitor_without_the_permission_is_refused(client, user, association):
    client.force_login(user)

    response = client.get(reverse("events:create"))

    assert response.status_code == 403


def test_an_editor_sees_the_form(editor_client, association):
    response = editor_client.get(reverse("events:create"))

    assert response.status_code == 200
    assert b"<form" in response.content


def test_the_navbar_offers_the_button_only_to_an_editor(editor_client, association):
    anonymous_content = Client().get(reverse("home")).content.decode()
    editor_content = editor_client.get(reverse("home")).content.decode()

    assert reverse("events:create") not in anonymous_content
    assert reverse("events:create") in editor_content


def test_an_editor_creates_an_event(editor_client, association):
    response = editor_client.post(reverse("events:create"), _post_data())

    event = Event.objects.get(title="Una giornata con gli asini")
    assert response.status_code == 302
    assert response.url == event.get_absolute_url()
    assert event.association == association
    assert event.slug == "una-giornata-con-gli-asini"
    local_start = timezone.localtime(event.starts_at)
    assert (local_start.date(), local_start.hour, local_start.minute) == (
        date(2027, 4, 20),
        16,
        0,
    )


def test_the_form_can_only_be_assigned_to_an_open_form(
    editor_client, association, public_form_factory
):
    open_form = public_form_factory(association=association, is_open=True)
    closed_form = public_form_factory(association=association, is_open=False)

    response = editor_client.get(reverse("events:create"))

    field = response.context["form"].fields["form"]
    assert open_form in field.queryset
    assert closed_form not in field.queryset


def test_the_description_is_sanitized(editor_client, association):
    editor_client.post(
        reverse("events:create"),
        _post_data(description="<p>Ciao</p><script>alert(1)</script>"),
    )

    event = Event.objects.get(title="Una giornata con gli asini")
    assert "<script>" not in event.description
    assert "<p>Ciao</p>" in event.description
