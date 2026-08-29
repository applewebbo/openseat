import pytest
from django.urls import reverse

from accounts.groups import ensure_editor_group, ensure_senior_editor_group

pytestmark = pytest.mark.django_db


def test_a_senior_editor_can_export_csv(
    senior_editor_client, event, submission, booking_factory, member_factory
):
    booking_factory(event=event, submission=submission)
    member_factory(
        association=event.association, submission=submission, first_name="Anna"
    )

    response = senior_editor_client.get(
        reverse("events:export-members", args=[event.slug]), {"format": "csv"}
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert b"Anna" in response.content


def test_xlsx_is_offered_too(senior_editor_client, event):
    response = senior_editor_client.get(
        reverse("events:export-members", args=[event.slug]), {"format": "xlsx"}
    )

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_only_first_time_joiners_are_included(
    senior_editor_client, event, submission, booking_factory, member_factory
):
    """Rebooking is not joining: only members whose submission is this
    event's booking count as acquired here."""
    old_member = member_factory(association=event.association, first_name="Vecchio")
    booking_factory(event=event, member=old_member)
    booking_factory(event=event, submission=submission)
    member_factory(
        association=event.association, submission=submission, first_name="Nuovo"
    )

    response = senior_editor_client.get(
        reverse("events:export-members", args=[event.slug]), {"format": "csv"}
    )

    assert b"Nuovo" in response.content
    assert b"Vecchio" not in response.content


def test_a_member_acquired_at_another_event_is_not_included(
    senior_editor_client,
    event,
    event_factory,
    submission,
    booking_factory,
    member_factory,
):
    other_event = event_factory(slug="altro-evento")
    booking_factory(event=other_event, submission=submission)
    member_factory(
        association=event.association, submission=submission, first_name="Altrove"
    )

    response = senior_editor_client.get(
        reverse("events:export-members", args=[event.slug]), {"format": "csv"}
    )

    assert b"Altrove" not in response.content


def test_an_editor_without_export_permission_is_refused(editor_client, event):
    response = editor_client.get(
        reverse("events:export-members", args=[event.slug]), {"format": "csv"}
    )

    assert response.status_code == 403


def test_an_anonymous_visitor_is_sent_to_log_in(client, event):
    response = client.get(
        reverse("events:export-members", args=[event.slug]), {"format": "csv"}
    )

    assert response.status_code == 302


def test_an_unknown_format_is_not_found(senior_editor_client, event):
    response = senior_editor_client.get(
        reverse("events:export-members", args=[event.slug]), {"format": "pdf"}
    )

    assert response.status_code == 404


def test_the_button_is_offered_only_to_a_senior_editor(client, user_factory, event):
    """Two independent users: sharing the `user` fixture would put both
    groups on the same row."""
    export_url = reverse("events:export-members", args=[event.slug])

    senior = user_factory(is_staff=True)
    senior.groups.add(ensure_senior_editor_group())
    client.force_login(senior)
    response = client.get(event.get_absolute_url(), {"view": "manage"})
    assert export_url in response.content.decode()
    client.logout()

    editor = user_factory(is_staff=True)
    editor.groups.add(ensure_editor_group())
    client.force_login(editor)
    response = client.get(event.get_absolute_url(), {"view": "manage"})
    assert export_url not in response.content.decode()
