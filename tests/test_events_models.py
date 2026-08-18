from datetime import timedelta

import pytest
import time_machine
from django.utils import timezone

from events.models import Booking

pytestmark = pytest.mark.django_db


def test_an_event_reads_as_its_title_and_day(event):
    assert event.title in str(event)
    assert event.starts_at.strftime("%d/%m/%Y") in str(event)


def test_bookings_are_open_before_the_event(event):
    assert event.is_open is True


def test_bookings_close_once_the_event_has_started(event):
    with time_machine.travel(event.starts_at + timedelta(minutes=1), tick=False):
        assert event.is_open is False


def test_an_unpublished_event_takes_no_bookings(event):
    event.is_published = False
    event.save()

    assert event.is_open is False


def test_an_event_has_no_capacity_limit(event, booking_factory, member_factory):
    """The association caps nothing: the count is for the organiser, not a gate."""
    for _ in range(50):
        booking_factory(event=event, member=member_factory(association=event.association))

    assert event.bookings.count() == 50
    assert event.is_open is True


def test_a_booking_names_who_is_coming(booking):
    assert booking.member.full_name in str(booking)


def test_cancelling_takes_a_booking_off_the_list(event, booking):
    booking.cancel()

    assert booking.cancelled_at is not None
    assert event.bookings.confirmed().count() == 0


def test_the_same_member_is_not_booked_twice(event, member, booking_factory):
    booking_factory(event=event, member=member)

    again = Booking.objects.book(event, member)

    assert event.bookings.confirmed().count() == 1
    assert again.pk == event.bookings.confirmed().get().pk


def test_booking_again_after_cancelling_revives_the_booking(event, member):
    first = Booking.objects.book(event, member)
    first.cancel()

    second = Booking.objects.book(event, member)

    assert second.pk == first.pk
    assert second.cancelled_at is None


def test_the_checklist_lists_confirmed_bookings_in_name_order(
    event, member_factory, booking_factory
):
    booking_factory(event=event, member=member_factory(association=event.association, last_name="Zani"))
    booking_factory(event=event, member=member_factory(association=event.association, last_name="Abbà"))

    names = [b.member.last_name for b in event.bookings.confirmed()]

    assert names == ["Abbà", "Zani"]


def test_an_event_starting_today_is_due_its_checklist(event_factory):
    event = event_factory(starts_at=timezone.localtime() + timedelta(hours=10))

    from events.models import Event

    assert event in Event.objects.due_for_checklist()


def test_an_event_next_week_is_not_due_yet(event_factory):
    from events.models import Event

    event_factory(starts_at=timezone.localtime() + timedelta(days=7))

    assert not Event.objects.due_for_checklist().exists()


def test_an_event_whose_checklist_went_out_is_not_due_again(event_factory):
    from events.models import Event

    event = event_factory(starts_at=timezone.localtime() + timedelta(hours=10))
    event.checklist_sent_at = timezone.now()
    event.save()

    assert not Event.objects.due_for_checklist().exists()


def test_the_organiser_sees_how_many_places_are_taken(
    staff_client, event, member_factory, booking_factory
):
    from django.urls import reverse

    booking_factory(event=event, member=member_factory(association=event.association))
    cancelled = booking_factory(
        event=event, member=member_factory(association=event.association)
    )
    cancelled.cancel()

    response = staff_client.get(reverse("admin:events_event_changelist"))

    assert response.status_code == 200
    assert event.bookings.confirmed().count() == 1


def test_bookings_are_listed_for_the_organiser(staff_client, booking):
    from django.urls import reverse

    response = staff_client.get(reverse("admin:events_booking_changelist"))

    assert response.status_code == 200
    assert booking.member.last_name.encode() in response.content
