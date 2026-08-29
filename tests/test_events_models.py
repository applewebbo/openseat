from datetime import datetime, time, timedelta

import pytest
import time_machine
from django.utils import timezone

from events.models import Booking, Event
from intake.models import BookingCloseMode

pytestmark = pytest.mark.django_db


def test_an_event_reads_as_its_title_and_day(event):
    assert event.title in str(event)
    assert event.starts_at.strftime("%d/%m/%Y") in str(event)


def test_the_slug_is_generated_from_the_title(association):
    event = Event.objects.create(
        association=association,
        title="Una giornata con gli asini",
        starts_at=timezone.now() + timedelta(days=7),
    )

    assert event.slug == "una-giornata-con-gli-asini"


def test_a_colliding_slug_gets_a_numeric_suffix(association):
    Event.objects.create(
        association=association, title="Festa", starts_at=timezone.now()
    )

    second = Event.objects.create(
        association=association, title="Festa", starts_at=timezone.now()
    )

    assert second.slug == "festa-2"


def test_the_slug_never_changes_once_set(event):
    original_slug = event.slug

    event.title = "Un titolo completamente diverso"
    event.save()

    assert event.slug == original_slug


def test_a_script_in_the_description_never_reaches_the_page(association):
    event = Event.objects.create(
        association=association,
        title="Evento",
        starts_at=timezone.now(),
        description="<p>Ciao</p><script>alert(1)</script>",
    )

    event.refresh_from_db()
    assert "<script>" not in event.description
    assert "<p>Ciao</p>" in event.description


def test_bookings_are_open_before_the_event(event):
    assert event.is_open is True


def test_bookings_close_at_midnight_before_the_event(event):
    midnight = timezone.make_aware(datetime.combine(event.starts_at.date(), time.min))
    with time_machine.travel(midnight, tick=False):
        assert event.is_open is False


def test_bookings_stay_open_up_to_the_last_minute_before_midnight(event):
    midnight = timezone.make_aware(datetime.combine(event.starts_at.date(), time.min))
    with time_machine.travel(midnight - timedelta(minutes=1), tick=False):
        assert event.is_open is True


def test_manual_mode_never_closes_bookings_on_the_clock(event):
    event.association.booking_close_mode = BookingCloseMode.MANUAL
    event.association.save()

    with time_machine.travel(event.starts_at + timedelta(days=1), tick=False):
        assert event.is_open is True


def test_start_time_mode_closes_bookings_at_the_event_start(event):
    event.association.booking_close_mode = BookingCloseMode.START_TIME
    event.association.save()

    with time_machine.travel(event.starts_at, tick=False):
        assert event.is_open is False
    with time_machine.travel(event.starts_at - timedelta(minutes=1), tick=False):
        assert event.is_open is True


def test_reopening_bookings_is_offered_before_the_cutoff(event):
    event.checkin_started_at = timezone.now()

    assert event.can_reopen_bookings is True


def test_reopening_bookings_is_refused_past_the_cutoff(event):
    midnight = timezone.make_aware(datetime.combine(event.starts_at.date(), time.min))
    with time_machine.travel(midnight, tick=False):
        event.checkin_started_at = timezone.now()

        assert event.can_reopen_bookings is False


def test_reopening_is_moot_when_check_in_was_never_opened(event):
    assert event.can_reopen_bookings is False


def test_an_unpublished_event_takes_no_bookings(event):
    event.is_published = False
    event.save()

    assert event.is_open is False


def test_check_in_closes_bookings_regardless_of_the_clock(event):
    event.checkin_started_at = timezone.now()

    assert event.is_open is False
    assert event.is_checkin_open is True


def test_an_event_with_no_check_in_yet_is_not_in_check_in(event):
    assert event.checkin_started_at is None
    assert event.is_checkin_open is False


def test_an_event_has_no_capacity_limit(event, booking_factory, member_factory):
    """The association caps nothing: the count is for the organiser, not a gate."""
    for _ in range(50):
        booking_factory(
            event=event, member=member_factory(association=event.association)
        )

    assert event.bookings.count() == 50
    assert event.is_open is True


def test_age_at_booking_is_a_snapshot_at_created_at(booking):
    booking.birth_date = datetime(2000, 6, 15).date()
    booking.created_at = timezone.make_aware(datetime(2026, 6, 14))

    assert booking.age_at_booking == 25

    booking.created_at = timezone.make_aware(datetime(2026, 6, 15))

    assert booking.age_at_booking == 26


def test_age_at_booking_is_none_without_a_birth_date(booking):
    booking.birth_date = None

    assert booking.age_at_booking is None


def test_a_booking_names_who_is_coming(booking):
    assert booking.member.full_name in str(booking)


def test_cancelling_takes_a_booking_off_the_list(event, booking):
    booking.cancel()

    assert booking.cancelled_at is not None
    assert event.bookings.active().count() == 0


def test_booking_a_member_snapshots_their_birth_date(event, member):
    member.birth_date = datetime(1990, 3, 2).date()
    member.save()

    booking = Booking.objects.book(event, member)

    assert booking.birth_date == member.birth_date


def test_booking_an_application_snapshots_the_subjects_birth_date(
    event, minor_submission
):
    booking = Booking.objects.book_application(event, minor_submission)

    assert booking.birth_date == minor_submission.member_birth_date


def test_the_same_member_is_not_booked_twice(event, member, booking_factory):
    booking_factory(event=event, member=member)

    again = Booking.objects.book(event, member)

    assert event.bookings.active().count() == 1
    assert again.pk == event.bookings.active().get().pk


def test_booking_again_after_cancelling_revives_the_booking(event, member):
    first = Booking.objects.book(event, member)
    first.cancel()

    second = Booking.objects.book(event, member)

    assert second.pk == first.pk
    assert second.cancelled_at is None


def test_the_checklist_lists_confirmed_bookings_in_name_order(
    event, member_factory, booking_factory
):
    booking_factory(
        event=event,
        member=member_factory(association=event.association, last_name="Zani"),
    )
    booking_factory(
        event=event,
        member=member_factory(association=event.association, last_name="Abbà"),
    )

    names = [b.member.last_name for b in event.bookings.active()]

    assert names == ["Abbà", "Zani"]


@time_machine.travel("2026-05-14 06:00+02:00", tick=False)
def test_an_event_starting_today_is_due_its_checklist(event_factory):
    """Pinned to a morning: run late in the evening, "in ten hours" is tomorrow."""
    event = event_factory(starts_at=timezone.localtime() + timedelta(hours=10))

    from events.models import Event

    assert event in Event.objects.due_for_checklist()


def test_an_event_next_week_is_not_due_yet(event_factory):
    from events.models import Event

    event_factory(starts_at=timezone.localtime() + timedelta(days=7))

    assert not Event.objects.due_for_checklist().exists()


def test_an_event_whose_checklist_went_out_is_not_due_again(event_factory):
    from events.models import Event

    with time_machine.travel("2026-05-14 06:00+02:00", tick=False):
        event = event_factory(starts_at=timezone.localtime() + timedelta(hours=10))
        event.checklist_sent_at = timezone.now()
        event.save()

        # Inside the frozen day: outside it, the event is simply not today and
        # the test would pass without proving anything about the stamp.
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
    assert event.bookings.active().count() == 1


def test_bookings_are_listed_for_the_organiser(staff_client, booking):
    from django.urls import reverse

    response = staff_client.get(reverse("admin:events_booking_changelist"))

    assert response.status_code == 200
    assert booking.member.last_name.encode() in response.content


# --- confirming a booking joins the register --------------------------------


def test_a_booking_from_the_register_needs_no_enrolling(booking_factory, member):
    booking = booking_factory(member=member)

    booking.confirmed_on = timezone.localdate()
    booking.fee_amount = 10
    booking.save()

    assert booking.member_id == member.pk
    assert booking.is_confirmed


def test_confirming_a_booking_from_an_application_enrols_the_applicant(
    event, minor_submission
):
    minor_submission.event = event
    minor_submission.submitted_at = timezone.now()
    minor_submission.save()
    booking = Booking.objects.book_application(event, minor_submission)

    booking.confirmed_on = timezone.localdate()
    booking.fee_amount = 10
    booking.save()

    assert booking.member is not None
    assert booking.member.first_name == "Luca"
    assert booking.member.submission_id == minor_submission.pk


def test_an_unconfirmed_booking_stays_off_the_register(event, minor_submission):
    minor_submission.event = event
    minor_submission.save()
    booking = Booking.objects.book_application(event, minor_submission)

    assert booking.member is None
    assert not booking.is_confirmed
