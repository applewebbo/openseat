from datetime import timedelta

import pytest
import time_machine
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from events.checklist import send_due_checklists

pytestmark = pytest.mark.django_db


def _event_today(event_factory, **kwargs):
    return event_factory(starts_at=timezone.localtime() + timedelta(hours=10), **kwargs)


def test_the_list_goes_out_on_the_day_of_the_event(
    event_factory, member_factory, booking_factory
):
    event = _event_today(event_factory)
    booking_factory(
        event=event, member=member_factory(association=event.association, last_name="Rossi")
    )

    send_due_checklists()

    sent = mail.outbox[-1]
    assert event.association.email in sent.to
    assert "Rossi" in sent.body


def test_the_list_is_not_sent_a_week_early(event_factory, booking_factory):
    event_factory(starts_at=timezone.localtime() + timedelta(days=7))

    send_due_checklists()

    assert not mail.outbox


def test_the_list_goes_out_once(event_factory):
    event = _event_today(event_factory)

    send_due_checklists()
    send_due_checklists()

    assert len(mail.outbox) == 1
    event.refresh_from_db()
    assert event.checklist_sent_at is not None


def test_an_unpublished_event_sends_nothing(event_factory):
    _event_today(event_factory, is_published=False)

    send_due_checklists()

    assert not mail.outbox


def test_a_cancelled_booking_is_off_the_list(
    event_factory, member_factory, booking_factory
):
    event = _event_today(event_factory)
    booking = booking_factory(
        event=event, member=member_factory(association=event.association, last_name="Ritirato")
    )
    booking.cancel()

    send_due_checklists()

    assert "Ritirato" not in mail.outbox[-1].body


def test_an_event_nobody_booked_still_gets_its_list(event_factory):
    """Whoever is on the door needs to know it is empty, not be left guessing."""
    _event_today(event_factory)

    send_due_checklists()

    assert len(mail.outbox) == 1


def test_the_list_carries_who_to_contact_for_each_member(
    event_factory, member_factory, booking_factory
):
    event = _event_today(event_factory)
    booking_factory(
        event=event,
        member=member_factory(
            association=event.association,
            contact_name="Maria Rossi",
            contact_phone="340 1234567",
        ),
    )

    send_due_checklists()

    body = mail.outbox[-1].body
    assert "Maria Rossi" in body
    assert "340 1234567" in body


def test_the_command_sends_the_due_lists(event_factory, capsys):
    _event_today(event_factory)

    call_command("send_checklists")

    assert len(mail.outbox) == 1
    assert "1" in capsys.readouterr().out


def test_the_nightly_job_can_be_registered():
    from django_q.models import Schedule

    call_command("events_schedule")

    schedule = Schedule.objects.get(name="events: pre-event checklist")
    assert schedule.func == "events.checklist.send_due_checklists"
    assert schedule.schedule_type == Schedule.DAILY


def test_registering_the_nightly_job_twice_leaves_one(monkeypatch):
    from django_q.models import Schedule

    call_command("events_schedule")
    call_command("events_schedule")

    assert Schedule.objects.filter(name="events: pre-event checklist").count() == 1


def test_the_job_is_set_to_run_at_midnight():
    """The list must be in hand before the day starts, not during it."""
    from django_q.models import Schedule

    call_command("events_schedule")

    next_run = timezone.localtime(Schedule.objects.get().next_run)
    assert (next_run.hour, next_run.minute) == (0, 5)


def test_time_travelling_past_midnight_sends_the_list(event_factory):
    """A job that fires at 00:05 must find the event that starts later today."""
    event = event_factory(
        starts_at=timezone.localtime().replace(hour=18, minute=0) + timedelta(days=1)
    )
    midnight = timezone.localtime(event.starts_at).replace(hour=0, minute=5)

    with time_machine.travel(midnight, tick=False):
        send_due_checklists()

    assert len(mail.outbox) == 1
