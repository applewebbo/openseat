from datetime import datetime, time

import pytest
import time_machine
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from intake.models import Subscription

pytestmark = pytest.mark.django_db


def _manual_booking_data(**overrides):
    data = {
        "subject_type": "self",
        "applicant_first_name": "Anna",
        "applicant_last_name": "Verdi",
        "applicant_birth_date": "1970-01-05",
        "applicant_birth_place": "Novara",
        "applicant_tax_code": "VRDNNA70A45F952I",
        "applicant_street": "Via Roma",
        "applicant_number": "1",
        "applicant_postcode": "28100",
        "applicant_city": "Novara",
        "applicant_phone": "3401234567",
        "applicant_email": "anna.verdi@example.com",
        "accepts_statute": "on",
        "sole_holder": "on",
        "consent_images": "on",
    }
    data.update(overrides)
    return data


def _minor_booking_data(**overrides):
    data = _manual_booking_data(
        subject_type="minor",
        member_first_name="Luca",
        member_last_name="Rossi",
        member_birth_date="2015-09-03",
        member_birth_place="Novara",
        member_tax_code="RSSLCU15P03F952V",
        member_street="Via Roma",
        member_number="4",
        member_city="Novara",
    )
    del data["sole_holder"]
    data.update(overrides)
    return data


# --- who sees the toggle -----------------------------------------------------


def test_an_anonymous_visitor_sees_no_checkin_controls(client, event):
    response = client.get(event.get_absolute_url())

    assert response.context["can_manage_checkin"] is False
    assert b"checkin-open" not in response.content


def test_a_staff_user_without_the_editor_group_sees_no_checkin_controls(
    client, user, event
):
    user.is_staff = True
    user.save()
    client.force_login(user)

    response = client.get(event.get_absolute_url())

    assert response.context["can_manage_checkin"] is False


def test_an_editor_sees_the_checkin_controls(editor_client, event):
    response = editor_client.get(event.get_absolute_url())

    assert response.context["can_manage_checkin"] is True
    assert (
        reverse("events:checkin-open", args=[event.slug]).encode() in response.content
    )


# --- the editor's bookings list, open or closed --------------------------------


def test_an_editor_always_sees_the_bookings_list(editor_client, event, booking_factory):
    booking = booking_factory(event=event)

    response = editor_client.get(event.get_absolute_url())

    assert response.templates[0].name == "events/checkin.html"
    assert booking.full_name in response.content.decode()


def test_no_checkin_button_shows_while_bookings_are_still_open(
    editor_client, event, booking_factory
):
    booking = booking_factory(event=event)

    response = editor_client.get(event.get_absolute_url())

    assert response.status_code == 200
    assert (
        reverse("events:checkin-confirm", args=[event.slug, booking.pk]).encode()
        not in response.content
    )


def test_checkin_button_shows_once_check_in_is_open(
    editor_client, event, booking_factory
):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))
    booking = booking_factory(event=event)

    response = editor_client.get(event.get_absolute_url())

    assert (
        reverse("events:checkin-confirm", args=[event.slug, booking.pk]).encode()
        in response.content
    )


def test_checking_in_is_refused_while_bookings_are_still_open(
    editor_client, event, booking_factory
):
    booking = booking_factory(event=event)

    response = editor_client.post(
        reverse("events:checkin-confirm", args=[event.slug, booking.pk])
    )

    assert response.status_code == 404
    booking.refresh_from_db()
    assert booking.is_confirmed is False


def test_a_public_visitor_still_sees_the_landing_page_once_auto_closed(event):
    midnight = timezone.make_aware(datetime.combine(event.starts_at.date(), time.min))
    with time_machine.travel(midnight, tick=False):
        response = Client().get(event.get_absolute_url())

        assert response.templates[0].name == "events/landing.html"
        assert event.title in response.content.decode()


# --- opening check-in ---------------------------------------------------------


def test_reopen_bookings_is_disabled_past_the_automatic_cutoff(editor_client, event):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))
    midnight = timezone.make_aware(datetime.combine(event.starts_at.date(), time.min))

    with time_machine.travel(midnight, tick=False):
        response = editor_client.get(event.get_absolute_url())

    assert b"disabled" in response.content


def test_an_editor_opens_check_in(editor_client, event):
    response = editor_client.post(reverse("events:checkin-open", args=[event.slug]))

    event.refresh_from_db()
    assert event.is_checkin_open is True
    assert response.status_code == 302
    assert response.url == event.get_absolute_url()


def test_opening_check_in_twice_keeps_the_first_timestamp(editor_client, event):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))
    event.refresh_from_db()
    first = event.checkin_started_at

    editor_client.post(reverse("events:checkin-open", args=[event.slug]))
    event.refresh_from_db()

    assert event.checkin_started_at == first


def test_a_visitor_without_permission_cannot_open_check_in(client, user, event):
    user.is_staff = True
    user.save()
    client.force_login(user)

    response = client.post(reverse("events:checkin-open", args=[event.slug]))

    assert response.status_code == 403
    event.refresh_from_db()
    assert event.is_checkin_open is False


def test_an_anonymous_visitor_cannot_open_check_in(client, event):
    response = client.post(reverse("events:checkin-open", args=[event.slug]))

    assert response.status_code == 302
    assert response.url.startswith(reverse("account_login"))
    event.refresh_from_db()
    assert event.is_checkin_open is False


# --- closing check-in ----------------------------------------------------------


def test_an_editor_closes_check_in(editor_client, event):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))

    response = editor_client.post(reverse("events:checkin-close", args=[event.slug]))

    event.refresh_from_db()
    assert event.is_checkin_open is False
    assert response.status_code == 302


def test_closing_check_in_when_it_was_never_opened_is_a_noop(editor_client, event):
    response = editor_client.post(reverse("events:checkin-close", args=[event.slug]))

    event.refresh_from_db()
    assert event.is_checkin_open is False
    assert response.status_code == 302


# --- effect on the public page --------------------------------------------------


def test_check_in_closes_the_public_booking_cta(client, event, editor_client):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))

    response = client.get(event.get_absolute_url())

    assert response.context["event"].is_open is False


# --- the roster replaces the landing page for an editor ------------------------


@pytest.fixture
def checked_in_event(event, editor_client):
    editor_client.post(reverse("events:checkin-open", args=[event.slug]))
    return event


def test_the_roster_shows_active_bookings(
    editor_client, checked_in_event, booking_factory
):
    booking = booking_factory(event=checked_in_event)

    response = editor_client.get(checked_in_event.get_absolute_url())

    assert response.templates[0].name == "events/checkin.html"
    assert booking.full_name in response.content.decode()


def test_the_roster_hides_a_cancelled_booking(
    editor_client, checked_in_event, booking_factory
):
    booking = booking_factory(event=checked_in_event)
    booking.cancel()

    response = editor_client.get(checked_in_event.get_absolute_url())

    assert booking.full_name not in response.content.decode()


def test_a_public_visitor_sees_no_roster_once_checkin_is_open(
    checked_in_event, booking_factory
):
    # A genuinely anonymous client: the `client` fixture would alias
    # `editor_client`'s session when both are requested in the same test.
    booking = booking_factory(event=checked_in_event)

    response = Client().get(checked_in_event.get_absolute_url())

    assert response.templates[0].name == "events/landing.html"
    assert booking.full_name not in response.content.decode()
    assert booking.contact_email not in response.content.decode()


def test_search_narrows_the_roster(editor_client, checked_in_event, booking_factory):
    match = booking_factory(
        event=checked_in_event, first_name="Giulia", last_name="Bianchi"
    )
    other = booking_factory(
        event=checked_in_event, first_name="Marco", last_name="Rossi"
    )

    response = editor_client.get(checked_in_event.get_absolute_url(), {"q": "Giulia"})

    content = response.content.decode()
    assert match.full_name in content
    assert other.full_name not in content


def test_an_htmx_search_returns_only_the_roster_fragment(
    editor_client, checked_in_event, booking_factory
):
    booking_factory(event=checked_in_event)

    response = editor_client.get(
        checked_in_event.get_absolute_url(), HTTP_HX_REQUEST="true"
    )

    assert response.templates[0].name == "events/checkin-roster-partial.html"
    assert b"<html" not in response.content


# --- the bookings summary card --------------------------------------------------


def test_the_summary_counts_bookings_and_confirmed(
    editor_client, event, booking_factory
):
    booking_factory(event=event, confirmed_on=timezone.localdate())
    booking_factory(event=event)

    response = editor_client.get(event.get_absolute_url())

    content = response.content.decode()
    assert 'id="booking-summary"' in content
    assert response.context["summary"]["total"] == 2
    assert response.context["summary"]["confirmed"] == 1


def test_the_summary_breaks_bookings_down_by_age_bracket(
    editor_client, event, booking_factory, age_bracket_factory
):
    young = age_bracket_factory(
        association=event.association, label="0-17", min_age=0, max_age=17
    )
    old = age_bracket_factory(
        association=event.association, label="18+", min_age=18, max_age=None
    )
    booking_factory(
        event=event,
        confirmed_on=timezone.localdate(),
        birth_date=timezone.localdate().replace(year=timezone.localdate().year - 10),
    )
    booking_factory(
        event=event,
        confirmed_on=None,
        birth_date=timezone.localdate().replace(year=timezone.localdate().year - 40),
    )
    booking_factory(
        event=event,
        confirmed_on=None,
        birth_date=timezone.localdate().replace(year=timezone.localdate().year - 10),
    )

    response = editor_client.get(event.get_absolute_url())

    summary = response.context["summary"]
    counts = dict(summary["brackets"])
    assert counts[young] == 2
    assert counts[old] == 1
    assert summary["unknown_booked"] == 0


def test_a_booking_with_no_birth_date_is_unknown_age(
    editor_client, event, booking_factory
):
    booking_factory(event=event, birth_date=None)
    booking_factory(event=event, birth_date=None)

    response = editor_client.get(event.get_absolute_url())

    assert response.context["summary"]["unknown_booked"] == 2


def test_the_summary_card_updates_via_the_htmx_oob_swap(
    editor_client, checked_in_event, booking_factory
):
    booking = booking_factory(event=checked_in_event)

    response = editor_client.post(
        reverse("events:checkin-confirm", args=[checked_in_event.slug, booking.pk]),
        HTTP_HX_REQUEST="true",
    )

    content = response.content.decode()
    assert 'id="booking-summary"' in content
    assert 'hx-swap-oob="true"' in content


# --- checking a booking in ------------------------------------------------------


def test_an_editor_checks_a_booking_in(
    editor_client, checked_in_event, booking_factory
):
    booking = booking_factory(event=checked_in_event)

    response = editor_client.post(
        reverse("events:checkin-confirm", args=[checked_in_event.slug, booking.pk])
    )

    booking.refresh_from_db()
    assert booking.is_confirmed
    assert booking.fee_amount == checked_in_event.association.membership_fee
    assert booking.fee_method == "cash"
    assert response.status_code == 302


def test_checking_in_twice_keeps_the_first_confirmation(
    editor_client, checked_in_event, booking_factory
):
    booking = booking_factory(event=checked_in_event)

    editor_client.post(
        reverse("events:checkin-confirm", args=[checked_in_event.slug, booking.pk])
    )
    booking.refresh_from_db()
    first = booking.confirmed_on

    editor_client.post(
        reverse("events:checkin-confirm", args=[checked_in_event.slug, booking.pk])
    )
    booking.refresh_from_db()

    assert booking.confirmed_on == first


def test_an_htmx_checkin_returns_the_row_fragment(
    editor_client, checked_in_event, booking_factory
):
    booking = booking_factory(event=checked_in_event)

    response = editor_client.post(
        reverse("events:checkin-confirm", args=[checked_in_event.slug, booking.pk]),
        HTTP_HX_REQUEST="true",
    )

    assert response.templates[0].name == "events/checkin-row-partial.html"
    assert f'id="booking-{booking.pk}"'.encode() in response.content


def test_an_editor_undoes_a_checkin(editor_client, checked_in_event, booking_factory):
    booking = booking_factory(event=checked_in_event)
    editor_client.post(
        reverse("events:checkin-confirm", args=[checked_in_event.slug, booking.pk])
    )

    response = editor_client.post(
        reverse("events:checkin-undo", args=[checked_in_event.slug, booking.pk])
    )

    booking.refresh_from_db()
    assert booking.is_confirmed is False
    assert booking.fee_amount is None
    assert response.status_code == 302


def test_undoing_is_a_noop_on_an_already_unconfirmed_booking(
    editor_client, checked_in_event, booking_factory
):
    booking = booking_factory(event=checked_in_event, confirmed_on=None)

    response = editor_client.post(
        reverse("events:checkin-undo", args=[checked_in_event.slug, booking.pk])
    )

    booking.refresh_from_db()
    assert booking.is_confirmed is False
    assert response.status_code == 302


def test_undoing_is_refused_while_bookings_are_still_open(
    editor_client, event, booking_factory
):
    booking = booking_factory(event=event, confirmed_on=timezone.localdate())

    response = editor_client.post(
        reverse("events:checkin-undo", args=[event.slug, booking.pk])
    )

    assert response.status_code == 404
    booking.refresh_from_db()
    assert booking.is_confirmed is True


def test_an_htmx_undo_returns_the_row_fragment_and_the_summary(
    editor_client, checked_in_event, booking_factory
):
    booking = booking_factory(event=checked_in_event)
    editor_client.post(
        reverse("events:checkin-confirm", args=[checked_in_event.slug, booking.pk])
    )

    response = editor_client.post(
        reverse("events:checkin-undo", args=[checked_in_event.slug, booking.pk]),
        HTTP_HX_REQUEST="true",
    )

    assert response.templates[0].name == "events/checkin-row-partial.html"
    content = response.content.decode()
    assert f'id="booking-{booking.pk}"' in content
    assert 'id="booking-summary"' in content
    assert 'hx-swap-oob="true"' in content


def test_a_visitor_without_permission_cannot_check_a_booking_in(
    checked_in_event, booking_factory, user_factory
):
    booking = booking_factory(event=checked_in_event)
    outsider = user_factory(is_staff=True)
    outsider_client = Client()
    outsider_client.force_login(outsider)

    response = outsider_client.post(
        reverse("events:checkin-confirm", args=[checked_in_event.slug, booking.pk])
    )

    assert response.status_code == 403
    booking.refresh_from_db()
    assert booking.is_confirmed is False


def test_checking_in_a_booking_from_another_event_is_not_found(
    editor_client, checked_in_event, event_factory, booking_factory
):
    other_event = event_factory()
    other_booking = booking_factory(event=other_event)

    response = editor_client.post(
        reverse(
            "events:checkin-confirm", args=[checked_in_event.slug, other_booking.pk]
        )
    )

    assert response.status_code == 404


# --- adding a booking by hand ---------------------------------------------------


def test_the_add_button_shows_even_while_bookings_are_open(
    editor_client, event, public_form
):
    event.form = public_form
    event.save()

    response = editor_client.get(event.get_absolute_url())

    assert reverse("events:checkin-add", args=[event.slug]).encode() in response.content


def test_an_editor_adds_a_self_booking(editor_client, event, public_form):
    event.form = public_form
    event.save()

    response = editor_client.post(
        reverse("events:checkin-add", args=[event.slug]), _manual_booking_data()
    )

    assert response.status_code == 302
    booking = event.bookings.active().get()
    assert booking.full_name == "Anna Verdi"
    assert booking.is_confirmed
    assert booking.fee_amount == event.association.membership_fee
    assert booking.fee_method == "cash"
    assert booking.member is not None
    assert booking.submission.state == booking.submission.State.SUBMITTED


def test_the_primary_signature_is_recorded(editor_client, event, public_form):
    event.form = public_form
    event.save()

    editor_client.post(
        reverse("events:checkin-add", args=[event.slug]), _manual_booking_data()
    )

    booking = event.bookings.active().get()
    subscription = booking.submission.subscriptions.get(role=Subscription.Role.PRIMARY)
    assert subscription.state == Subscription.State.SIGNED


def test_adding_a_minor_booking_with_a_sole_holder(editor_client, event, public_form):
    event.form = public_form
    event.save()

    response = editor_client.post(
        reverse("events:checkin-add", args=[event.slug]),
        _minor_booking_data(sole_holder="on"),
    )

    assert response.status_code == 302
    booking = event.bookings.active().get()
    assert booking.full_name == "Luca Rossi"
    assert booking.member.tax_code == "RSSLCU15P03F952V"
    assert not booking.submission.subscriptions.filter(
        role=Subscription.Role.SECOND_PARENT
    ).exists()


def test_adding_a_minor_booking_with_two_holders_signs_the_second_parent(
    editor_client, event, public_form
):
    event.form = public_form
    event.save()

    editor_client.post(
        reverse("events:checkin-add", args=[event.slug]),
        _minor_booking_data(
            second_parent_first_name="Paolo",
            second_parent_last_name="Rossi",
        ),
    )

    booking = event.bookings.active().get()
    assert booking.submission.sole_holder is False
    assert booking.submission.image_consent_active is True
    second_parent = booking.submission.subscriptions.get(
        role=Subscription.Role.SECOND_PARENT
    )
    assert second_parent.state == Subscription.State.SIGNED
    assert second_parent.signatory_name == "Paolo Rossi"


def test_a_minor_booking_needs_the_members_details(editor_client, event, public_form):
    event.form = public_form
    event.save()

    response = editor_client.post(
        reverse("events:checkin-add", args=[event.slug]),
        _manual_booking_data(subject_type="minor"),
    )

    assert response.status_code == 200
    assert response.context["add_form"].errors
    assert event.bookings.active().count() == 0


def test_a_minor_booking_with_two_holders_needs_the_second_parent(
    editor_client, event, public_form
):
    event.form = public_form
    event.save()

    response = editor_client.post(
        reverse("events:checkin-add", args=[event.slug]),
        _minor_booking_data(),
    )

    assert response.status_code == 200
    assert "second_parent_first_name" in response.context["add_form"].errors
    assert event.bookings.active().count() == 0


def test_a_booking_without_the_statute_accepted_is_rejected(
    editor_client, event, public_form
):
    event.form = public_form
    event.save()
    data = _manual_booking_data()
    del data["accepts_statute"]

    response = editor_client.post(
        reverse("events:checkin-add", args=[event.slug]), data
    )

    assert response.status_code == 200
    assert event.bookings.active().count() == 0


def test_a_visitor_without_permission_cannot_add_a_booking(
    checked_in_event, user_factory
):
    outsider = user_factory(is_staff=True)
    outsider_client = Client()
    outsider_client.force_login(outsider)

    response = outsider_client.post(
        reverse("events:checkin-add", args=[checked_in_event.slug]),
        _manual_booking_data(),
    )

    assert response.status_code == 403
    assert checked_in_event.bookings.active().count() == 0


def test_an_anonymous_visitor_cannot_add_a_booking(event):
    response = Client().post(
        reverse("events:checkin-add", args=[event.slug]), _manual_booking_data()
    )

    assert response.status_code == 302
    assert response.url.startswith(reverse("account_login"))


def test_the_lookup_finds_a_minor_and_prefills_their_own_fields(
    editor_client, event, member_factory
):
    member = member_factory(
        association=event.association,
        first_name="Luca",
        last_name="Rossi",
        tax_code="RSSLCU15P03F952V",
        birth_date="2015-09-03",
        street="Via Roma",
        number="4",
        city="Novara",
    )

    response = editor_client.get(
        reverse("events:checkin-lookup", args=[event.slug]),
        {"existing_tax_code": member.tax_code},
    )

    content = response.content.decode()
    assert (
        response.templates[0].name == "events/checkin-add-existing-search-partial.html"
    )
    assert "choice = 'minor'" in content
    assert member.full_name in content
    assert 'hx-swap-oob="true"' in content
    assert 'id="member-fields"' in content
    assert 'value="Luca"' in content
    assert 'value="Rossi"' in content
    assert "border-success" in content


def test_the_lookup_also_prefills_the_signers_own_details_for_a_minor(
    editor_client, event, member_factory
):
    member_factory(
        association=event.association,
        first_name="Luca",
        last_name="Rossi",
        tax_code="RSSLCU15P03F952V",
        birth_date="2015-09-03",
        contact_name="Maria Rossi",
        contact_email="maria.rossi@example.com",
        contact_phone="3401234567",
        street="Via Roma",
        number="4",
        city="Novara",
    )

    response = editor_client.get(
        reverse("events:checkin-lookup", args=[event.slug]),
        {"existing_tax_code": "RSSLCU15P03F952V"},
    )

    content = response.content.decode()
    assert 'id="applicant-fields"' in content
    assert 'value="Maria"' in content
    assert 'value="Rossi"' in content
    assert 'value="maria.rossi@example.com"' in content
    assert 'value="Via Roma"' in content


def test_the_lookup_finds_an_adult_and_prefills_their_own_details_only(
    editor_client, event, member_factory
):
    member_factory(
        association=event.association,
        first_name="Anna",
        last_name="Verdi",
        tax_code="VRDNNA70A45F952I",
        birth_date="1970-01-05",
        contact_email="anna.verdi@example.com",
    )

    response = editor_client.get(
        reverse("events:checkin-lookup", args=[event.slug]),
        {"existing_tax_code": "VRDNNA70A45F952I"},
    )

    content = response.content.decode()
    assert "choice = 'self'" in content
    assert 'id="applicant-fields"' in content
    assert 'value="Anna"' in content
    assert 'id="member-fields"' not in content


def test_the_lookup_with_no_match_shows_a_message_and_keeps_the_typed_code(
    editor_client, event
):
    response = editor_client.get(
        reverse("events:checkin-lookup", args=[event.slug]),
        {"existing_tax_code": "VRDNNA70A45F952I"},
    )

    content = response.content.decode()
    assert (
        response.templates[0].name == "events/checkin-add-existing-search-partial.html"
    )
    assert 'value="VRDNNA70A45F952I"' in content
    assert "border-success" not in content
    assert "Nessun socio trovato" in content
