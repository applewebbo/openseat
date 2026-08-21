import datetime

import pytest
import time_machine
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from events.access import contact_token_for

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_throttle():
    """The throttle outlives a test unless it is cleared: it lives in the cache."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def booked(event, booking_factory, member_factory):
    return booking_factory(
        event=event,
        member=member_factory(association=event.association),
        first_name="Luca",
        last_name="Rossi",
        contact_email="maria.rossi@example.com",
    )


def ask_for_link(client, email="maria.rossi@example.com"):
    return client.post(reverse("events:recover"), {"email": email})


# --- asking for the link ----------------------------------------------------


def test_an_address_with_a_booking_is_sent_the_link(client, booked):
    ask_for_link(client)

    assert len(mail.outbox) == 1
    assert "maria.rossi@example.com" in mail.outbox[0].to
    assert reverse("events:mine", args=[contact_token_for(booked.contact_email)]) in (
        mail.outbox[0].body
    )


def test_the_answer_never_says_whether_the_address_booked(client, booked):
    """Telling the two apart would let anybody test an address at a time."""
    found = ask_for_link(client)
    cache.clear()
    missing = ask_for_link(client, "nessuno@example.com")

    assert found.url == missing.url == reverse("events:recover-sent")
    page = client.get(found.url).content.decode()
    assert "Se questo indirizzo corrisponde" in page


def test_an_address_with_no_booking_is_sent_nothing(client, booked):
    ask_for_link(client, "nessuno@example.com")

    assert not mail.outbox


def test_a_cancelled_booking_is_not_worth_a_link(client, booked):
    booked.cancel()

    ask_for_link(client)

    assert not mail.outbox


def test_a_booking_for_a_past_date_is_not_worth_a_link(client, booked):
    with time_machine.travel(
        booked.event.starts_at + datetime.timedelta(hours=1), tick=False
    ):
        ask_for_link(client)

    assert not mail.outbox


def test_an_unpublished_event_is_not_worth_a_link(client, booked):
    booked.event.is_published = False
    booked.event.save()

    ask_for_link(client)

    assert not mail.outbox


def test_a_malformed_address_is_a_field_error_not_a_send(client, booked):
    response = client.post(reverse("events:recover"), {"email": "non-una-mail"})

    assert response.status_code == 200
    assert "email" in response.context["form"].errors
    assert not mail.outbox


def test_the_page_stands_on_its_own(client, association):
    response = client.get(reverse("events:recover"))

    assert response.status_code == 200


# --- the throttle -----------------------------------------------------------


def test_asking_twice_in_a_row_sends_one_mail(client, booked):
    """The card mails whatever address is typed, so it must not be a megaphone."""
    ask_for_link(client)
    ask_for_link(client)

    assert len(mail.outbox) == 1


def test_the_throttled_answer_looks_the_same(client, booked):
    ask_for_link(client)

    response = ask_for_link(client)

    assert response.url == reverse("events:recover-sent")


def test_the_window_lets_go_eventually(client, booked, settings):
    settings.EVENTS_BOOKING_LINK_THROTTLE_SECONDS = 300
    ask_for_link(client)

    with time_machine.travel(
        timezone.now() + datetime.timedelta(seconds=301), tick=False
    ):
        cache.clear()  # locmem expiry reads the real clock, not the frozen one
        ask_for_link(client)

    assert len(mail.outbox) == 2


def test_one_address_does_not_throttle_another(client, booked, booking_factory):
    booking_factory(event=booked.event, contact_email="altro@example.com")

    ask_for_link(client)
    ask_for_link(client, "altro@example.com")

    assert len(mail.outbox) == 2


# --- the link ---------------------------------------------------------------


def test_the_link_lists_every_booking_that_address_holds(
    client, booked, event_factory, booking_factory
):
    other = event_factory(slug="altra-data", association=booked.event.association)
    booking_factory(
        event=other,
        first_name="Sara",
        last_name="Rossi",
        contact_email="maria.rossi@example.com",
    )

    response = client.get(
        reverse("events:mine", args=[contact_token_for("maria.rossi@example.com")])
    )

    names = {booking.full_name for booking in response.context["bookings"]}
    assert names == {"Luca Rossi", "Sara Rossi"}


def test_the_link_shows_nobody_elses_booking(client, booked, booking_factory):
    booking_factory(
        event=booked.event,
        first_name="Estranea",
        last_name="Bianchi",
        contact_email="altro@example.com",
    )

    response = client.get(
        reverse("events:mine", args=[contact_token_for("maria.rossi@example.com")])
    )

    assert [b.full_name for b in response.context["bookings"]] == ["Luca Rossi"]


def test_the_link_leaves_past_dates_out(client, booked, event_factory, booking_factory):
    gone = event_factory(
        slug="passata",
        association=booked.event.association,
        starts_at=timezone.now() - datetime.timedelta(days=3),
    )
    booking_factory(
        event=gone,
        first_name="Vecchia",
        last_name="Rossi",
        contact_email="maria.rossi@example.com",
    )

    response = client.get(
        reverse("events:mine", args=[contact_token_for("maria.rossi@example.com")])
    )

    assert [b.full_name for b in response.context["bookings"]] == ["Luca Rossi"]


def test_the_link_lets_the_booking_be_cancelled(client, booked):
    client.get(reverse("events:mine", args=[contact_token_for(booked.contact_email)]))

    client.post(reverse("events:cancel", args=[booked.event.slug, booked.pk]))

    booked.refresh_from_db()
    assert booked.cancelled_at is not None


def test_a_tampered_link_asks_for_a_new_one(client, association):
    response = client.get(reverse("events:mine", args=["inventato"]))

    assert response.status_code == 200
    assert response.context["link_expired"] is True


def test_the_link_dies_after_a_week(client, booked, settings):
    settings.EVENTS_BOOKING_LINK_DAYS = 7
    url = reverse("events:mine", args=[contact_token_for(booked.contact_email)])

    with time_machine.travel(
        timezone.now() + datetime.timedelta(days=8), tick=False
    ):
        response = client.get(url)

    assert response.context["link_expired"] is True


def test_a_link_for_an_address_with_nothing_left_says_so(client, booked):
    booked.cancel()

    response = client.get(
        reverse("events:mine", args=[contact_token_for(booked.contact_email)])
    )

    assert not response.context["bookings"]
    assert "nulla di prenotato" in response.content.decode()


# --- the card on the home page ----------------------------------------------


def test_the_home_page_offers_the_card(client, association):
    content = client.get(reverse("home")).content.decode()

    assert reverse("events:recover") in content
    assert "Gestisci le tue prenotazioni" in content
