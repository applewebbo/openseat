import datetime

import pytest
import time_machine
from django.utils import timezone

from events.maintenance import purge_stale_bookings, stale_bookings
from events.models import Booking

pytestmark = pytest.mark.django_db


@pytest.fixture
def past_event(event_factory):
    return event_factory(starts_at=timezone.now() - datetime.timedelta(days=45))


def test_an_unconfirmed_booking_for_a_long_past_event_is_stale(
    past_event, booking_factory
):
    booking = booking_factory(event=past_event)

    assert booking in stale_bookings()


def test_a_confirmed_booking_is_never_stale(past_event, booking_factory):
    booking = booking_factory(
        event=past_event, confirmed_on=timezone.localdate(), fee_amount=10
    )

    assert booking not in stale_bookings()


def test_a_booking_for_a_recent_event_is_not_stale_yet(event, booking_factory):
    booking = booking_factory(event=event)

    assert booking not in stale_bookings()


def test_purging_deletes_the_booking_and_its_application(
    past_event, minor_submission
):
    minor_submission.event = past_event
    minor_submission.save()
    booking = Booking.objects.book_application(past_event, minor_submission)

    purged = purge_stale_bookings()

    assert purged == 1
    assert not Booking.objects.filter(pk=booking.pk).exists()
    assert not minor_submission._meta.model.objects.filter(
        pk=minor_submission.pk
    ).exists()


def test_purging_leaves_the_member_booked_path_alone(past_event, booking_factory):
    """No application to delete: the register-member path never made one."""
    booking = booking_factory(event=past_event)

    purge_stale_bookings()

    assert not Booking.objects.filter(pk=booking.pk).exists()


def test_purging_a_recent_bookings_event_leaves_it_be(event, booking_factory):
    booking_factory(event=event)

    purged = purge_stale_bookings()

    assert purged == 0


def test_the_sweep_setting_moves_the_cutoff(settings, event_factory, booking_factory):
    settings.EVENTS_BOOKING_SWEEP_DAYS = 1
    just_over_a_day = event_factory(
        starts_at=timezone.now() - datetime.timedelta(days=2)
    )
    booking = booking_factory(event=just_over_a_day)

    assert booking in stale_bookings()


def test_time_travelling_past_the_cutoff_makes_a_booking_stale(event, booking_factory):
    booking = booking_factory(event=event)

    with time_machine.travel(
        event.starts_at + datetime.timedelta(days=31), tick=False
    ):
        assert booking in stale_bookings()
