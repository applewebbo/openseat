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


def test_an_editor_sees_the_form(editor_client, public_form):
    response = editor_client.get(reverse("events:create"))

    assert response.status_code == 200
    assert b"<form" in response.content


def test_the_navbar_offers_the_button_only_to_an_editor(editor_client, association):
    anonymous_content = Client().get(reverse("home")).content.decode()
    editor_content = editor_client.get(reverse("home")).content.decode()

    assert reverse("events:create") not in anonymous_content
    assert reverse("events:create") in editor_content


def test_without_an_open_form_the_page_shows_a_notice_instead(
    editor_client, association, public_form_factory
):
    public_form_factory(association=association, is_open=False)

    response = editor_client.get(reverse("events:create"))

    assert response.status_code == 200
    assert b"<form" not in response.content
    assert b'method="post"' not in response.content


def test_an_editor_creates_an_event(editor_client, public_form):
    response = editor_client.post(reverse("events:create"), _post_data())

    event = Event.objects.get(title="Una giornata con gli asini")
    assert response.status_code == 302
    assert response.url == event.get_absolute_url()
    assert event.association == public_form.association
    assert event.slug == "una-giornata-con-gli-asini"
    local_start = timezone.localtime(event.starts_at)
    assert (local_start.date(), local_start.hour, local_start.minute) == (
        date(2027, 4, 20),
        16,
        0,
    )


def test_an_editor_sets_the_estimated_duration(editor_client, public_form):
    editor_client.post(reverse("events:create"), _post_data(duration_hours="3"))

    event = Event.objects.get(title="Una giornata con gli asini")
    assert event.duration_hours == 3


def test_with_one_open_form_the_field_is_hidden_and_assigned(
    editor_client, public_form
):
    response = editor_client.get(reverse("events:create"))
    assert "form" not in response.context["form"].fields

    editor_client.post(reverse("events:create"), _post_data())

    event = Event.objects.get(title="Una giornata con gli asini")
    assert event.form == public_form


def test_with_several_open_forms_the_field_offers_a_choice(
    editor_client, association, public_form_factory
):
    open_form = public_form_factory(association=association, is_open=True)
    other_open_form = public_form_factory(association=association, is_open=True)
    closed_form = public_form_factory(association=association, is_open=False)

    response = editor_client.get(reverse("events:create"))

    field = response.context["form"].fields["form"]
    assert open_form in field.queryset
    assert other_open_form in field.queryset
    assert closed_form not in field.queryset


def test_with_several_open_forms_the_selected_one_is_saved(
    editor_client, association, public_form_factory
):
    public_form_factory(association=association, is_open=True)
    other_open_form = public_form_factory(association=association, is_open=True)

    editor_client.post(reverse("events:create"), _post_data(form=other_open_form.pk))

    event = Event.objects.get(title="Una giornata con gli asini")
    assert event.form == other_open_form


def test_the_default_form_is_preselected_when_open(
    editor_client, association, public_form_factory
):
    public_form_factory(association=association, is_open=True)
    default_form = public_form_factory(
        association=association, is_open=True, is_default=True
    )

    response = editor_client.get(reverse("events:create"))

    assert response.context["form"].fields["form"].initial == default_form.pk


def test_a_closed_default_form_is_not_preselected(
    editor_client, association, public_form_factory
):
    public_form_factory(association=association, is_open=True)
    public_form_factory(association=association, is_open=True)
    public_form_factory(association=association, is_open=False, is_default=True)

    response = editor_client.get(reverse("events:create"))

    assert response.context["form"].fields["form"].initial is None


def test_the_location_is_prefilled_from_the_association_default(
    editor_client, association, public_form
):
    association.default_location = "Ca' di Asu, Olengo"
    association.save()

    response = editor_client.get(reverse("events:create"))

    assert response.context["form"].fields["location"].initial == "Ca' di Asu, Olengo"


def test_invalid_data_redisplays_the_form_with_errors(editor_client, public_form):
    response = editor_client.post(reverse("events:create"), _post_data(title=""))

    assert response.status_code == 200
    assert response.context["form"].errors
    assert not Event.objects.exists()


def test_the_description_is_sanitized(editor_client, public_form):
    editor_client.post(
        reverse("events:create"),
        _post_data(description="<p>Ciao</p><script>alert(1)</script>"),
    )

    event = Event.objects.get(title="Una giornata con gli asini")
    assert "<script>" not in event.description
    assert "<p>Ciao</p>" in event.description
