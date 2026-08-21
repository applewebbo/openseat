import datetime

import pytest
import time_machine
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from events.access import token_for
from events.notifications import deliver_booking_confirmation

pytestmark = pytest.mark.django_db


@pytest.fixture
def family(member_factory, event):
    """Two children on the register, both reachable at the same parent address."""
    shared = {
        "association": event.association,
        "contact_email": "maria.rossi@example.com",
        "contact_name": "Maria Rossi",
    }
    luca = member_factory(
        first_name="Luca", last_name="Rossi", tax_code="RSSLCU15P03F952V", **shared
    )
    sara = member_factory(
        first_name="Sara", last_name="Rossi", tax_code="RSSSRA18A41F952G", **shared
    )
    return luca, sara


def book_as_member(client, event, family):
    client.post(
        reverse("events:identify", args=[event.slug]),
        {"email": "maria.rossi@example.com", "tax_code": "RSSLCU15P03F952V"},
    )
    return client.post(
        reverse("events:book", args=[event.slug]),
        {"members": [str(member.pk) for member in family]},
    )


def confirmation(event, email="maria.rossi@example.com"):
    """The booking confirmation, told apart from the membership receipt that
    goes to the same address in the same breath."""
    return next(m for m in mail.outbox if email in m.to and event.title in m.subject)


# --- the confirmation ------------------------------------------------------


def test_booking_a_place_is_confirmed_by_mail(client, event, family):
    book_as_member(client, event, family)

    sent = confirmation(event)
    assert event.title in sent.subject
    assert "Luca Rossi" in sent.body
    assert "Sara Rossi" in sent.body


def test_the_confirmation_says_when_and_where(client, event, family):
    book_as_member(client, event, family)

    body = confirmation(event).body
    assert event.location in body
    assert event.starts_at.astimezone().strftime("%d/%m/%Y") in body


def test_the_confirmation_lists_only_who_was_ticked(client, event, family):
    luca, _sara = family

    book_as_member(client, event, [luca])

    body = confirmation(event).body
    assert "Luca Rossi" in body
    assert "Sara Rossi" not in body


def test_changing_the_booking_later_is_not_confirmed_again(client, event, family):
    """The page says what was saved. A second mail saying the same thing is noise."""
    luca, _sara = family
    book_as_member(client, event, family)
    mail.outbox.clear()

    client.post(reverse("events:book", args=[event.slug]), {"members": [str(luca.pk)]})

    assert not mail.outbox


def test_the_links_in_the_mail_are_absolute(client, event, family, settings):
    settings.SITE_BASE_URL = "https://soci.example.org"

    book_as_member(client, event, family)

    assert "https://soci.example.org/evento/" in confirmation(event).body


def test_the_confirmation_goes_out_as_html_too(client, event, family):
    book_as_member(client, event, family)

    sent = confirmation(event)
    html, content_type = sent.alternatives[0]
    assert content_type == "text/html"
    assert event.title in html


def test_joining_to_book_is_confirmed_too(client, event, minor_submission):
    """Somebody who books by applying to join hears about the place as well."""
    event.association = minor_submission.form.association
    event.save()
    minor_submission.event = event
    minor_submission.save()

    client.post(
        reverse("intake:submit", args=[minor_submission.token]),
        {"place": "Novara", "declaration": "on"},
    )

    sent = confirmation(event, minor_submission.applicant_email)
    assert event.title in sent.subject
    assert "Luca Rossi" in sent.body


def test_joining_to_book_is_one_mail_and_not_two(client, event, minor_submission):
    """The confirmation carries what the receipt carried, so the receipt itself
    would be a second mail about the same act."""
    event.association = minor_submission.form.association
    event.save()
    minor_submission.event = event
    minor_submission.save()

    client.post(
        reverse("intake:submit", args=[minor_submission.token]),
        {"place": "Novara", "declaration": "on"},
    )

    to_applicant = [m for m in mail.outbox if minor_submission.applicant_email in m.to]
    assert len(to_applicant) == 1
    body = to_applicant[0].body
    assert reverse("intake:done", args=[minor_submission.token]) in body
    assert "10" in body


def test_an_application_with_no_event_confirms_nothing(client, event, minor_submission):
    client.post(
        reverse("intake:submit", args=[minor_submission.token]),
        {"place": "Novara", "declaration": "on"},
    )

    assert not [m for m in mail.outbox if event.title in m.subject]


# --- the link back into the booking ----------------------------------------


def manage_url(event, email="maria.rossi@example.com"):
    return reverse("events:manage", args=[event.slug, token_for(event, email)])


def test_the_link_opens_the_booking_page_without_asking_again(client, event, family):
    book_as_member(client, event, family)
    client.cookies.clear()

    response = client.get(manage_url(event), follow=True)

    assert response.status_code == 200
    names = {booking.full_name for booking in response.context["bookings"]}
    assert names == {"Luca Rossi", "Sara Rossi"}


def test_the_link_cancels_one_place_without_touching_the_rest(client, event, family):
    luca, sara = family
    book_as_member(client, event, family)
    client.cookies.clear()

    client.get(manage_url(event))
    luca_booking = event.bookings.active().get(member=luca)
    client.post(reverse("events:cancel", args=[event.slug, luca_booking.pk]))

    assert set(event.bookings.active().values_list("member_id", flat=True)) == {sara.pk}
    assert luca.bookings.get().cancelled_at is not None


def test_the_link_dies_with_the_event(client, event, family):
    """And says so in its own words: whoever follows it had a place, so the
    generic "write to the organisers" of a closed event reads as a brush-off."""
    url = manage_url(event)

    with time_machine.travel(event.starts_at + datetime.timedelta(hours=1), tick=False):
        response = client.get(url)

    assert response.status_code == 200
    page = response.content.decode()
    assert "già passato" in page
    assert "non accetta più prenotazioni" not in page


def test_a_tampered_link_is_not_found(client, event, family):
    response = client.get(reverse("events:manage", args=[event.slug, "made-up-token"]))

    assert response.status_code == 404


def test_a_link_for_another_event_does_not_open_this_one(
    client, event, event_factory, family
):
    other = event_factory(slug="altro-evento", association=event.association)

    response = client.get(
        reverse(
            "events:manage",
            args=[other.slug, token_for(event, family[0].contact_email)],
        )
    )

    assert response.status_code == 404


def test_a_link_for_somebody_off_the_register_opens_nothing(client, event, family):
    response = client.get(manage_url(event, "nessuno@example.com"))

    assert response.status_code == 302
    assert response.url == event.get_absolute_url()


# --- editing contacts and a note --------------------------------------------


def test_the_link_lets_you_update_contacts_and_a_note(client, event, family):
    luca, _sara = family
    book_as_member(client, event, [luca])
    client.cookies.clear()

    client.get(manage_url(event))
    booking = event.bookings.active().get(member=luca)
    client.post(
        reverse("events:edit", args=[event.slug, booking.pk]),
        {
            "contact_name": "Maria Rossi",
            "contact_email": "nuova.maria@example.com",
            "contact_phone": "3491112233",
            "note": "Allergica alle noci",
        },
    )

    booking.refresh_from_db()
    assert booking.contact_email == "nuova.maria@example.com"
    assert booking.contact_phone == "3491112233"
    assert booking.note == "Allergica alle noci"


def test_editing_with_an_invalid_email_changes_nothing(client, event, family):
    luca, _sara = family
    book_as_member(client, event, [luca])
    client.cookies.clear()
    client.get(manage_url(event))
    booking = event.bookings.active().get(member=luca)

    client.post(
        reverse("events:edit", args=[event.slug, booking.pk]),
        {"contact_name": "Maria Rossi", "contact_email": "not-an-email"},
    )

    booking.refresh_from_db()
    assert booking.contact_email == "maria.rossi@example.com"


def test_editing_someone_elses_booking_is_refused(
    client, event, family, member_factory, booking_factory
):
    stranger = member_factory(
        association=event.association, contact_email="altro@example.com"
    )
    stranger_booking = booking_factory(event=event, member=stranger)
    book_as_member(client, event, family)
    client.cookies.clear()
    client.get(manage_url(event))

    response = client.post(
        reverse("events:edit", args=[event.slug, stranger_booking.pk]),
        {"contact_name": "Nessuno", "contact_email": "nessuno@example.com"},
    )

    assert response.url == event.get_absolute_url()
    stranger_booking.refresh_from_db()
    assert stranger_booking.contact_email == "altro@example.com"


def test_editing_after_the_event_started_is_not_found(client, event, family):
    luca, _sara = family
    book_as_member(client, event, [luca])
    client.cookies.clear()
    client.get(manage_url(event))
    booking = event.bookings.active().get(member=luca)

    with time_machine.travel(event.starts_at + datetime.timedelta(hours=1), tick=False):
        response = client.post(
            reverse("events:edit", args=[event.slug, booking.pk]),
            {"contact_name": "Maria Rossi", "contact_email": "maria.rossi@example.com"},
        )

    assert response.status_code == 404


def test_a_queued_confirmation_of_nothing_is_not_sent(client, event, family):
    """The queue runs after the request: by then the last place may be gone."""
    book_as_member(client, event, family)
    event.bookings.update(cancelled_at=timezone.now())
    mail.outbox.clear()

    deliver_booking_confirmation(event.pk, "maria.rossi@example.com")

    assert not mail.outbox
