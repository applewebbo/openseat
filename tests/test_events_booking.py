import pytest
from django.urls import reverse

from events.models import Booking
from intake.models import Submission

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


def _identify(client, event, **overrides):
    data = {
        "email": "maria.rossi@example.com",
        "tax_code": "RSSLCU15P03F952V",
    }
    data.update(overrides)
    return client.post(reverse("events:identify", args=[event.slug]), data)


# --- the event page --------------------------------------------------------


def test_the_event_page_needs_no_account(client, event):
    response = client.get(event.get_absolute_url())

    assert response.status_code == 200
    assert event.title in response.content.decode()


def test_an_unpublished_event_is_not_found(client, event):
    event.is_published = False
    event.save()

    assert client.get(event.get_absolute_url()).status_code == 404


def test_an_event_that_has_started_says_bookings_are_closed(client, event, settings):
    from datetime import timedelta

    import time_machine

    with time_machine.travel(event.starts_at + timedelta(hours=1), tick=False):
        response = client.get(event.get_absolute_url())

        assert response.status_code == 200
        assert response.context["event"].is_open is False


# --- identifying a member --------------------------------------------------


def test_the_right_pair_opens_the_booking_step(client, event, family):
    response = _identify(client, event)

    assert response.status_code == 302
    assert response.url == reverse("events:book", args=[event.slug])


def test_the_tax_code_is_checked_not_just_the_address(client, event, family):
    response = _identify(client, event, tax_code="RSSMRA85D52F952F")

    assert response.status_code == 200
    assert response.context["form"].errors


def test_an_address_nobody_uses_is_refused(client, event, family):
    response = _identify(client, event, email="sconosciuto@example.com")

    assert response.status_code == 200
    assert response.context["form"].errors


def test_the_tax_code_is_read_regardless_of_case(client, event, family):
    response = _identify(client, event, tax_code="rsslcu15p03f952v")

    assert response.status_code == 302


def test_a_member_of_another_association_does_not_open_this_event(
    client, event, member_factory, association_factory
):
    member_factory(
        association=association_factory(slug="altra"),
        contact_email="maria.rossi@example.com",
        tax_code="RSSLCU15P03F952V",
    )

    response = _identify(client, event)

    assert response.status_code == 200
    assert response.context["form"].errors


# --- booking ---------------------------------------------------------------


def test_the_whole_family_is_offered_once_one_of_them_is_proven(client, event, family):
    """A parent who knows one child's tax code manages the others too."""
    _identify(client, event)

    response = client.get(reverse("events:book", args=[event.slug]))

    offered = {member.first_name for member in response.context["members"]}
    assert offered == {"Luca", "Sara"}


def test_booking_without_identifying_first_sends_you_back(client, event, family):
    response = client.get(reverse("events:book", args=[event.slug]))

    assert response.status_code == 302
    assert response.url == event.get_absolute_url()


def test_places_are_booked_for_everyone_ticked(client, event, family):
    luca, sara = family
    _identify(client, event)

    client.post(
        reverse("events:book", args=[event.slug]),
        {"members": [str(luca.pk), str(sara.pk)]},
    )

    assert event.bookings.active().count() == 2


def test_ticking_nobody_asks_again(client, event, family):
    _identify(client, event)

    response = client.post(reverse("events:book", args=[event.slug]), {"members": []})

    assert response.status_code == 200
    assert not event.bookings.exists()


def test_unticking_somebody_cancels_their_place(client, event, family):
    luca, sara = family
    _identify(client, event)
    client.post(
        reverse("events:book", args=[event.slug]),
        {"members": [str(luca.pk), str(sara.pk)]},
    )

    client.post(reverse("events:book", args=[event.slug]), {"members": [str(luca.pk)]})

    booked = [b.member for b in event.bookings.active()]
    assert booked == [luca]


def test_nobody_can_book_a_member_from_another_family(
    client, event, family, member_factory
):
    stranger = member_factory(
        association=event.association, contact_email="altro@example.com"
    )
    _identify(client, event)

    client.post(
        reverse("events:book", args=[event.slug]), {"members": [str(stranger.pk)]}
    )

    assert not Booking.objects.filter(member=stranger).exists()


def test_a_booking_confirms_who_is_coming(client, event, family):
    luca, _sara = family
    _identify(client, event)

    client.post(reverse("events:book", args=[event.slug]), {"members": [str(luca.pk)]})
    response = client.get(reverse("events:booked", args=[event.slug]))

    assert response.status_code == 200
    assert b"Luca" in response.content


def test_bookings_are_refused_once_the_event_has_started(client, event, family):
    from datetime import timedelta

    import time_machine

    luca, _sara = family
    _identify(client, event)

    with time_machine.travel(event.starts_at + timedelta(hours=1), tick=False):
        response = client.post(
            reverse("events:book", args=[event.slug]), {"members": [str(luca.pk)]}
        )

    assert response.status_code == 404
    assert not event.bookings.exists()


# --- joining in order to book ----------------------------------------------


def test_somebody_new_is_sent_to_the_application(client, event, public_form_factory):
    public_form_factory(association=event.association, slug="adesione")

    response = client.post(reverse("events:join", args=[event.slug]))

    submission = Submission.objects.get()
    assert submission.event == event
    assert response.url.startswith(f"/richiesta/{submission.token}/")


def test_joining_for_an_event_books_the_place_on_submission(
    client, event, public_form_factory, minor_submission
):
    minor_submission.event = event
    minor_submission.save()

    client.post(
        reverse("intake:submit", args=[minor_submission.token]),
        {"place": "Novara", "declaration": "on"},
    )

    booking = event.bookings.active().get()
    assert booking.first_name == "Luca"
    assert booking.member is None


def test_a_second_open_form_does_not_break_joining(client, event, public_form_factory):
    """An association may run more than one public form; the newest open one is
    the application in use."""
    public_form_factory(association=event.association, slug="adesione-2024")
    current = public_form_factory(association=event.association, slug="adesione-2025")

    response = client.post(reverse("events:join", args=[event.slug]))

    assert response.status_code == 302
    assert Submission.objects.get().form == current


def test_a_closed_form_is_never_the_one_used(client, event, public_form_factory):
    open_form = public_form_factory(association=event.association, slug="adesione")
    public_form_factory(association=event.association, slug="archiviata", is_open=False)

    client.post(reverse("events:join", args=[event.slug]))

    assert Submission.objects.get().form == open_form


def test_an_association_with_no_application_form_cannot_take_new_members(client, event):
    response = client.post(reverse("events:join", args=[event.slug]))

    assert response.status_code == 404


def test_an_invalid_tax_code_stops_before_the_register_is_queried(
    client, event, family
):
    """A malformed code is a field error, not a "no such member" answer."""
    response = _identify(client, event, tax_code="non-un-codice")

    assert response.status_code == 200
    assert "tax_code" in response.context["form"].errors


# --- calling one place off --------------------------------------------------


def test_cancelling_drops_only_the_chosen_place(client, event, family):
    luca, sara = family
    _identify(client, event)
    client.post(
        reverse("events:book", args=[event.slug]),
        {"members": [str(luca.pk), str(sara.pk)]},
    )
    luca_booking = event.bookings.active().get(member=luca)

    response = client.post(reverse("events:cancel", args=[event.slug, luca_booking.pk]))

    assert response.url == reverse("events:booked", args=[event.slug])
    assert [b.member for b in event.bookings.active()] == [sara]


def test_cancelling_leaves_the_other_families_alone(
    client, event, family, member_factory, booking_factory
):
    stranger = member_factory(
        association=event.association, contact_email="altro@example.com"
    )
    booking_factory(event=event, member=stranger)
    _identify(client, event)
    client.post(
        reverse("events:book", args=[event.slug]), {"members": [str(family[0].pk)]}
    )
    own_booking = event.bookings.active().get(member=family[0])

    client.post(reverse("events:cancel", args=[event.slug, own_booking.pk]))

    assert [b.member for b in event.bookings.active()] == [stranger]


def test_cancelling_someone_elses_booking_is_refused(
    client, event, family, member_factory, booking_factory
):
    stranger = member_factory(
        association=event.association, contact_email="altro@example.com"
    )
    stranger_booking = booking_factory(event=event, member=stranger)
    _identify(client, event)

    response = client.post(
        reverse("events:cancel", args=[event.slug, stranger_booking.pk])
    )

    assert response.url == event.get_absolute_url()
    assert event.bookings.active().filter(pk=stranger_booking.pk).exists()


def test_cancelling_without_identifying_first_sends_you_back(
    client, event, family, booking_factory
):
    booking = booking_factory(event=event, member=family[0])

    response = client.post(reverse("events:cancel", args=[event.slug, booking.pk]))

    assert response.url == event.get_absolute_url()


def test_a_cancellation_after_the_event_started_is_not_found(client, event, family):
    from datetime import timedelta

    import time_machine

    _identify(client, event)
    client.post(
        reverse("events:book", args=[event.slug]), {"members": [str(family[0].pk)]}
    )
    booking = event.bookings.active().get(member=family[0])

    with time_machine.travel(event.starts_at + timedelta(hours=1), tick=False):
        response = client.post(reverse("events:cancel", args=[event.slug, booking.pk]))

    assert response.status_code == 404
    assert event.bookings.active().count() == 1


def test_cancelling_says_so_rather_than_showing_an_empty_list(client, event, family):
    _identify(client, event)
    client.post(
        reverse("events:book", args=[event.slug]), {"members": [str(family[0].pk)]}
    )
    booking = event.bookings.active().get(member=family[0])

    client.post(reverse("events:cancel", args=[event.slug, booking.pk]))
    response = client.get(reverse("events:booked", args=[event.slug]))

    assert "annullata" in response.content.decode()
