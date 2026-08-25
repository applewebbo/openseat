import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


# --- who sees the toggle -----------------------------------------------------


def test_an_anonymous_visitor_sees_no_checkin_controls(client, event):
    response = client.get(event.get_absolute_url())

    assert response.context["can_manage_checkin"] is False
    assert b"checkin-open" not in response.content


def test_a_staff_user_without_the_editor_group_sees_no_checkin_controls(
    client, user, event
):
    user.is_staff = True
    user.save()
    client.force_login(user)

    response = client.get(event.get_absolute_url())

    assert response.context["can_manage_checkin"] is False


def test_an_editor_sees_the_checkin_controls(editor_client, event):
    response = editor_client.get(event.get_absolute_url())

    assert response.context["can_manage_checkin"] is True
    assert reverse("events:checkin-open", args=[event.slug]).encode() in response.content


# --- opening check-in ---------------------------------------------------------


def test_an_editor_opens_check_in(editor_client, event):
    response = editor_client.post(reverse("events:checkin-open", args=[event.slug]))

    event.refresh_from_db()
    assert event.is_checkin_open is True
    assert response.status_code == 302
    assert response.url == event.get_absolute_url()


def test_opening_check_in_twice_keeps_the_first_timestamp(editor_client, event):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))
    event.refresh_from_db()
    first = event.checkin_started_at

    editor_client.post(reverse("events:checkin-open", args=[event.slug]))
    event.refresh_from_db()

    assert event.checkin_started_at == first


def test_a_visitor_without_permission_cannot_open_check_in(client, user, event):
    user.is_staff = True
    user.save()
    client.force_login(user)

    response = client.post(reverse("events:checkin-open", args=[event.slug]))

    assert response.status_code == 403
    event.refresh_from_db()
    assert event.is_checkin_open is False


def test_an_anonymous_visitor_cannot_open_check_in(client, event):
    response = client.post(reverse("events:checkin-open", args=[event.slug]))

    assert response.status_code == 302
    assert response.url.startswith(reverse("account_login"))
    event.refresh_from_db()
    assert event.is_checkin_open is False


# --- closing check-in ----------------------------------------------------------


def test_an_editor_closes_check_in(editor_client, event):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))

    response = editor_client.post(reverse("events:checkin-close", args=[event.slug]))

    event.refresh_from_db()
    assert event.is_checkin_open is False
    assert response.status_code == 302


def test_closing_check_in_when_it_was_never_opened_is_a_noop(editor_client, event):
    response = editor_client.post(reverse("events:checkin-close", args=[event.slug]))

    event.refresh_from_db()
    assert event.is_checkin_open is False
    assert response.status_code == 302


# --- effect on the public page --------------------------------------------------


def test_check_in_closes_the_public_booking_cta(client, event, editor_client):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))

    response = client.get(event.get_absolute_url())

    assert response.context["event"].is_open is False
