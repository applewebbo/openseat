import datetime

import pytest
from django.contrib.admin.sites import AdminSite
from django.core import mail
from django.db import connection
from django.forms import modelformset_factory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from events.admin import EventAdmin
from events.models import Booking, Event
from intake.models import PublicForm

pytestmark = pytest.mark.django_db


@pytest.fixture
def spring_event(event_factory, association):
    """An event on a date with a weekday worth leaving out."""
    return event_factory(
        association=association,
        title="Festa di primavera",
        slug="festa-di-primavera",
        starts_at=timezone.make_aware(datetime.datetime(2026, 4, 20, 16, 0)),
    )


def _changelist(staff_client):
    response = staff_client.get(reverse("admin:events_event_changelist"))
    assert response.status_code == 200
    return response.content.decode()


def test_the_date_is_compact_and_carries_no_weekday(staff_client, spring_event):
    content = _changelist(staff_client)

    assert "20/04/2026 16:00" in content
    assert "Lunedì" not in content


def test_the_date_column_is_called_date(staff_client, spring_event):
    content = _changelist(staff_client)

    assert "column-starts_on" in content
    assert "Inizia il" not in content


def test_the_association_is_not_a_column(staff_client, spring_event):
    """One installation, one association: the same name on every row says nothing."""
    content = _changelist(staff_client)

    assert "field-association" not in content


def test_the_checklist_column_is_called_sent(staff_client, spring_event):
    content = _changelist(staff_client)

    assert "column-sent_on" in content
    assert "Lista inviata il" not in content


def test_the_dates_to_filter_by_sit_in_the_filter_card(staff_client, spring_event):
    """The month links belong with the other filters, not above the table."""
    content = _changelist(staff_client)

    card = content.split('id="changelist-filter"')[1].split("</search>")[0]
    assert "date-hierarchy" in card
    assert "Per data" in card
    assert "Filter by" not in content


def test_the_columns_are_named_in_italian(staff_client, spring_event):
    """The labels come from the project catalogue, so a stale .mo shows here."""
    content = _changelist(staff_client)

    assert ">Data</a>" in content
    assert ">Inviata</a>" in content


def test_booked_column_shows_only_active_bookings(
    staff_client, spring_event, booking_factory
):
    booking_factory(event=spring_event, cancelled_at=None)
    booking_factory(event=spring_event, cancelled_at=timezone.now())

    content = _changelist(staff_client)

    assert ">1<" in content.split('class="field-booked"')[1][:20]


def test_changelist_query_count_is_stable_with_more_events(
    staff_client, association, event_factory, booking_factory
):
    one = event_factory(association=association)
    booking_factory(event=one)
    with CaptureQueriesContext(connection) as ctx:
        _changelist(staff_client)
    baseline = len(ctx.captured_queries)

    for _ in range(9):
        booking_factory(event=event_factory(association=association))
    with CaptureQueriesContext(connection) as ctx:
        _changelist(staff_client)

    assert len(ctx.captured_queries) == baseline


def test_only_open_forms_are_offered_for_the_event(
    staff_client, spring_event, public_form_factory
):
    open_form = public_form_factory(association=spring_event.association)
    closed_form = public_form_factory(
        association=spring_event.association, is_open=False
    )

    response = staff_client.get(
        reverse("admin:events_event_change", args=[spring_event.pk])
    )

    options = response.context["adminform"].form.fields["form"].queryset
    assert open_form in options
    assert closed_form not in options


def test_the_slug_is_neither_editable_nor_shown(staff_client, spring_event):
    response = staff_client.get(
        reverse("admin:events_event_change", args=[spring_event.pk])
    )

    assert "slug" not in response.context["adminform"].form.fields
    assert b'name="slug"' not in response.content


# --- the confirmation mail ---------------------------------------------------


def _booking_add_data(event, **overrides):
    data = {
        "event": event.pk,
        "first_name": "Anna",
        "last_name": "Verdi",
        "contact_email": "anna.verdi@example.com",
        "fee_method": "",
        "send_confirmation": "on",
    }
    data.update(overrides)
    return data


def test_adding_a_booking_from_the_admin_sends_the_confirmation(staff_client, event):
    response = staff_client.post(
        reverse("admin:events_booking_add"), _booking_add_data(event)
    )

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["anna.verdi@example.com"]


def test_unticking_the_checkbox_skips_the_confirmation_mail(staff_client, event):
    data = _booking_add_data(event)
    del data["send_confirmation"]

    response = staff_client.post(reverse("admin:events_booking_add"), data)

    assert response.status_code == 302
    assert not mail.outbox


def test_editing_an_existing_booking_does_not_resend_the_confirmation(
    staff_client, booking
):
    response = staff_client.post(
        reverse("admin:events_booking_change", args=[booking.pk]),
        {
            "event": booking.event_id,
            "first_name": booking.first_name,
            "last_name": booking.last_name,
            "contact_email": booking.contact_email,
            "fee_method": "",
            "send_confirmation": "on",
        },
    )

    assert response.status_code == 302
    assert not mail.outbox


# --- the booking inline on the event change form -----------------------------


def _bookings_management_data(total=0, initial=0):
    return {
        "bookings-TOTAL_FORMS": str(total),
        "bookings-INITIAL_FORMS": str(initial),
        "bookings-MIN_NUM_FORMS": "0",
        "bookings-MAX_NUM_FORMS": "1000",
    }


def _event_post_data(event, **overrides):
    local_start = timezone.localtime(event.starts_at)
    data = {
        "association": event.association_id,
        "form": "",
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "starts_at_0": local_start.date().isoformat(),
        "starts_at_1": local_start.time().isoformat(),
        "duration_hours": "",
        "is_published": "on" if event.is_published else "",
        "checkin_started_at_0": "",
        "checkin_started_at_1": "",
        "cost": event.cost if event.cost is not None else "",
    }
    data.update(_bookings_management_data())
    data.update(overrides)
    return data


def test_adding_a_booking_through_the_event_inline_sends_the_confirmation(
    staff_client, event
):
    data = _event_post_data(
        event,
        **_bookings_management_data(total=1),
        **{
            "bookings-0-first_name": "Anna",
            "bookings-0-last_name": "Verdi",
            "bookings-0-contact_email": "anna.verdi@example.com",
            "bookings-0-fee_method": "",
            "bookings-0-send_confirmation": "on",
        },
    )

    response = staff_client.post(
        reverse("admin:events_event_change", args=[event.pk]), data
    )

    assert response.status_code == 302, response.context["adminform"].form.errors
    assert event.bookings.filter(first_name="Anna").exists()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["anna.verdi@example.com"]


def test_deleting_a_booking_through_the_event_inline_removes_it(
    staff_client, event, booking_factory
):
    to_delete = booking_factory(event=event)

    data = _event_post_data(
        event,
        **_bookings_management_data(total=1, initial=1),
        **{
            "bookings-0-id": to_delete.pk,
            "bookings-0-first_name": to_delete.first_name,
            "bookings-0-last_name": to_delete.last_name,
            "bookings-0-contact_email": to_delete.contact_email,
            "bookings-0-fee_method": "",
            "bookings-0-DELETE": "on",
        },
    )

    response = staff_client.post(
        reverse("admin:events_event_change", args=[event.pk]), data
    )

    assert response.status_code == 302, response.context["adminform"].form.errors
    assert not Booking.objects.filter(pk=to_delete.pk).exists()


def test_save_formset_leaves_non_booking_formsets_to_django(
    rf, event, public_form_factory
):
    """The guard exists because inlines besides bookings run through here too."""
    open_form = public_form_factory(association=event.association)
    FormSet = modelformset_factory(PublicForm, fields=("title",))
    formset = FormSet(
        data={
            **{
                f"form-{key}": value
                for key, value in {
                    "TOTAL_FORMS": "1",
                    "INITIAL_FORMS": "1",
                    "MIN_NUM_FORMS": "0",
                    "MAX_NUM_FORMS": "1000",
                }.items()
            },
            "form-0-id": open_form.pk,
            "form-0-title": "Modulo rinominato",
        },
        queryset=PublicForm.objects.filter(pk=open_form.pk),
    )
    assert formset.is_valid(), formset.errors
    request = rf.post(reverse("admin:events_event_change", args=[event.pk]))
    admin_instance = EventAdmin(Event, AdminSite())

    admin_instance.save_formset(request, form=None, formset=formset, change=True)

    open_form.refresh_from_db()
    assert open_form.title == "Modulo rinominato"
