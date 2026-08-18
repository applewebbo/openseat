from datetime import timedelta

import pytest
import time_machine
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from intake.maintenance import purge_expired_drafts, remind_stale_drafts
from intake.models import SectionKey, Submission

pytestmark = pytest.mark.django_db


def _landing(public_form):
    return public_form.get_absolute_url()


def _begin(public_form):
    return reverse("intake:begin", args=[public_form.slug])


# --- session recognition ---------------------------------------------------


def test_starting_remembers_the_draft_on_this_device(client, public_form):
    client.post(_begin(public_form))

    submission = Submission.objects.get()
    assert client.session["intake_draft"] == str(submission.token)


def test_coming_back_is_offered_the_draft_already_open(client, public_form):
    client.post(_begin(public_form))

    response = client.get(_landing(public_form))

    assert response.context["resumable"] == Submission.objects.get()


def test_coming_back_can_still_start_a_fresh_request(client, public_form):
    client.post(_begin(public_form))

    client.post(_begin(public_form))

    assert Submission.objects.count() == 2


def test_a_stranger_is_offered_nothing(client, public_form):
    response = client.get(_landing(public_form))

    assert response.context["resumable"] is None


def test_a_sent_request_is_not_offered_as_a_draft(client, minor_submission):
    session = client.session
    session["intake_draft"] = str(minor_submission.token)
    session.save()
    client.post(
        reverse("intake:submit", args=[minor_submission.token]),
        {"place": "Novara", "declaration": "on"},
    )

    response = client.get(_landing(minor_submission.form))

    assert response.context["resumable"] is None


def test_a_draft_from_another_form_is_not_offered_here(
    client, public_form, public_form_factory
):
    client.post(_begin(public_form))
    other = public_form_factory(slug="altro-modulo")

    response = client.get(_landing(other))

    assert response.context["resumable"] is None


def test_a_forgotten_draft_does_not_break_the_landing_page(client, public_form):
    session = client.session
    session["intake_draft"] = "3f1d2e4a-0000-4000-8000-000000000000"
    session.save()

    response = client.get(_landing(public_form))

    assert response.status_code == 200
    assert response.context["resumable"] is None


# --- save for later --------------------------------------------------------


def test_every_step_offers_to_save_for_later(client, minor_submission):
    response = client.get(
        reverse("intake:step", args=[minor_submission.token, SectionKey.APPLICANT])
    )

    assert (
        reverse("intake:save", args=[minor_submission.token])
        in response.content.decode()
    )


def test_the_save_page_shows_the_link_to_come_back_to(client, minor_submission):
    response = client.get(reverse("intake:save", args=[minor_submission.token]))

    assert response.status_code == 200
    assert str(minor_submission.token) in response.content.decode()


def test_the_known_address_is_offered_ready_to_send(client, minor_submission):
    response = client.get(reverse("intake:save", args=[minor_submission.token]))

    assert response.context["form"]["email"].value() == minor_submission.applicant_email


def test_saving_for_later_emails_the_link(client, minor_submission):
    response = client.post(
        reverse("intake:save", args=[minor_submission.token]),
        {"email": "maria.rossi@example.com"},
    )

    sent = next(m for m in mail.outbox if "maria.rossi@example.com" in m.to)
    assert str(minor_submission.token) in sent.body
    assert response.status_code == 302


def test_an_early_draft_can_be_saved_by_giving_an_address(client, submission):
    client.post(
        reverse("intake:save", args=[submission.token]),
        {"email": "chi.sono@example.com"},
    )

    assert [m for m in mail.outbox if "chi.sono@example.com" in m.to]


def test_saving_without_an_address_asks_for_one(client, submission):
    response = client.post(reverse("intake:save", args=[submission.token]), {})

    assert response.status_code == 200
    assert response.context["form"].errors
    assert not mail.outbox


def test_a_sent_request_has_nothing_left_to_save(client, minor_submission):
    client.post(
        reverse("intake:submit", args=[minor_submission.token]),
        {"place": "Novara", "declaration": "on"},
    )

    response = client.get(reverse("intake:save", args=[minor_submission.token]))

    assert response.status_code == 302


# --- the reminder ----------------------------------------------------------


def test_a_draft_touched_moments_ago_is_left_alone(minor_submission):
    remind_stale_drafts()

    assert not mail.outbox
    minor_submission.refresh_from_db()
    assert minor_submission.reminder_sent_at is None


def test_a_draft_left_for_a_day_gets_one_reminder(minor_submission):
    with time_machine.travel(timezone.now() + timedelta(hours=25), tick=False):
        remind_stale_drafts()

    minor_submission.refresh_from_db()
    assert minor_submission.reminder_sent_at is not None
    assert [m for m in mail.outbox if minor_submission.applicant_email in m.to]


def test_the_reminder_is_never_sent_twice(minor_submission):
    with time_machine.travel(timezone.now() + timedelta(hours=25), tick=False):
        remind_stale_drafts()
        sent_once = len(mail.outbox)
        remind_stale_drafts()

    assert len(mail.outbox) == sent_once


def test_a_draft_with_no_address_yet_cannot_be_reminded(submission):
    with time_machine.travel(timezone.now() + timedelta(hours=25), tick=False):
        remind_stale_drafts()

    assert not mail.outbox


def test_a_sent_request_is_never_reminded(client, minor_submission):
    client.post(
        reverse("intake:submit", args=[minor_submission.token]),
        {"place": "Novara", "declaration": "on"},
    )
    mail.outbox.clear()

    with time_machine.travel(timezone.now() + timedelta(hours=25), tick=False):
        remind_stale_drafts()

    assert not mail.outbox


def test_an_expired_draft_is_not_worth_reminding(minor_submission):
    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        remind_stale_drafts()

    assert not mail.outbox


# --- expiry ----------------------------------------------------------------


def test_a_draft_expires_thirty_days_after_its_last_change(minor_submission):
    assert minor_submission.is_expired is False

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        assert minor_submission.is_expired is True


def test_an_expired_draft_says_so_instead_of_opening(client, minor_submission):
    url = reverse("intake:step", args=[minor_submission.token, SectionKey.APPLICANT])

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        response = client.get(url)

    assert response.status_code == 410


def test_an_expired_draft_cannot_be_signed(client, minor_submission):
    url = reverse("intake:submit", args=[minor_submission.token])

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        response = client.post(url, {"place": "Novara", "declaration": "on"})

    minor_submission.refresh_from_db()
    assert response.status_code == 410
    assert minor_submission.state == Submission.State.DRAFT


def test_an_expired_draft_is_not_offered_on_return(client, public_form):
    client.post(_begin(public_form))

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        response = client.get(_landing(public_form))

    assert response.context["resumable"] is None


def test_expired_drafts_are_deleted_rather_than_kept(minor_submission):
    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        purge_expired_drafts()

    assert not Submission.objects.filter(pk=minor_submission.pk).exists()


def test_a_sent_request_is_never_purged(client, minor_submission):
    client.post(
        reverse("intake:submit", args=[minor_submission.token]),
        {"place": "Novara", "declaration": "on"},
    )

    with time_machine.travel(timezone.now() + timedelta(days=400), tick=False):
        purge_expired_drafts()

    assert Submission.objects.filter(pk=minor_submission.pk).exists()


def test_the_hourly_sweep_can_be_registered():
    """Reminders and expiry are worthless if nothing ever calls them."""
    from django.core.management import call_command
    from django_q.models import Schedule

    call_command("intake_schedule")

    schedule = Schedule.objects.get(name="intake: draft maintenance")
    assert schedule.func == "intake.maintenance.run_draft_maintenance"
    assert schedule.schedule_type == Schedule.HOURLY
    assert schedule.repeats == -1


def test_registering_the_sweep_twice_leaves_one_job():
    from django.core.management import call_command
    from django_q.models import Schedule

    call_command("intake_schedule")
    call_command("intake_schedule")

    assert Schedule.objects.filter(name="intake: draft maintenance").count() == 1


def test_the_sweep_reports_what_it_did(minor_submission):
    from intake.maintenance import run_draft_maintenance

    with time_machine.travel(timezone.now() + timedelta(hours=25), tick=False):
        result = run_draft_maintenance()

    assert result == {"reminded": 1, "purged": 0}


def test_an_expired_draft_cannot_be_reviewed(client, minor_submission):
    url = reverse("intake:review", args=[minor_submission.token])

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        response = client.get(url)

    assert response.status_code == 410


def test_an_expired_draft_offers_no_link_to_come_back_to(client, minor_submission):
    url = reverse("intake:save", args=[minor_submission.token])

    with time_machine.travel(timezone.now() + timedelta(days=31), tick=False):
        response = client.get(url)

    assert response.status_code == 410


def test_the_sent_page_confirms_where_the_link_went(client, minor_submission):
    client.post(
        reverse("intake:save", args=[minor_submission.token]),
        {"email": "maria.rossi@example.com"},
    )

    response = client.get(reverse("intake:saved", args=[minor_submission.token]))

    assert response.status_code == 200
    assert (
        reverse("intake:step", args=[minor_submission.token, SectionKey.REVIEW])
        in response.content.decode()
    )
