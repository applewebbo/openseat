from datetime import date

import pytest
from django.urls import reverse

from members.models import Member
from members.register import enrol

pytestmark = pytest.mark.django_db


def _submit(client, submission):
    return client.post(
        reverse("intake:submit", args=[submission.token]),
        {"place": "Novara", "declaration": "on"},
    )


# --- who ends up on the register -------------------------------------------


def test_submitting_puts_the_child_on_the_register(client, minor_submission):
    _submit(client, minor_submission)

    member = Member.objects.get()
    assert (member.first_name, member.last_name) == ("Luca", "Rossi")
    assert member.tax_code == "RSSLCU15P03F952V"


def test_the_parent_is_the_contact_for_a_child(client, minor_submission):
    """The child is the member; the parent is who the association writes to."""
    _submit(client, minor_submission)

    member = Member.objects.get()
    assert member.contact_email == "maria.rossi@example.com"
    assert member.contact_name == "Maria Rossi"


def test_an_adult_applying_alone_is_their_own_contact(client, adult_submission):
    _submit(client, adult_submission)

    member = Member.objects.get()
    assert (member.first_name, member.last_name) == ("Anna", "Verdi")
    assert member.contact_email == member.email
    assert member.contact_name == "Anna Verdi"


def test_the_register_records_when_the_person_joined(client, minor_submission):
    _submit(client, minor_submission)

    assert Member.objects.get().joined_on == date.today()


def test_a_new_member_is_not_ratified_yet(client, minor_submission):
    """Submitting makes a member; the board ratifies afterwards, in its own time."""
    _submit(client, minor_submission)

    member = Member.objects.get()
    assert member.ratified_on is None
    assert member.is_active is True


def test_the_register_keeps_the_application_it_came_from(client, minor_submission):
    _submit(client, minor_submission)

    assert Member.objects.get().submission == minor_submission


def test_a_draft_puts_nobody_on_the_register(minor_submission):
    assert not Member.objects.exists()


def test_enrolling_the_same_application_twice_adds_one_member(minor_submission):
    minor_submission.state = minor_submission.State.SUBMITTED
    minor_submission.save()

    enrol(minor_submission)
    enrol(minor_submission)

    assert Member.objects.count() == 1


# --- the register is a document of its own ---------------------------------


def test_correcting_the_register_leaves_the_signed_application_alone(
    client, minor_submission
):
    """The request is a signed document; the register is maintained over years."""
    _submit(client, minor_submission)
    member = Member.objects.get()

    member.last_name = "Rossi Bianchi"
    member.save()

    minor_submission.refresh_from_db()
    assert minor_submission.member_last_name == "Rossi"


def test_a_member_reads_as_their_full_name(member):
    assert str(member) == f"{member.first_name} {member.last_name}"


# --- one contact, several members ------------------------------------------


def test_one_parent_can_have_several_children_on_the_register(
    member_factory, association
):
    parent = "maria.rossi@example.com"
    member_factory(association=association, first_name="Luca", contact_email=parent)
    member_factory(association=association, first_name="Sara", contact_email=parent)

    assert Member.objects.for_contact(association, parent).count() == 2


def test_the_lookup_ignores_case_and_stray_spaces(member_factory, association):
    member_factory(association=association, contact_email="maria.rossi@example.com")

    found = Member.objects.for_contact(association, "  Maria.Rossi@Example.com ")

    assert found.count() == 1


def test_an_unknown_email_matches_nobody(member_factory, association):
    member_factory(association=association, contact_email="maria@example.com")

    assert not Member.objects.for_contact(association, "chi@example.com").exists()


def test_a_member_of_another_association_is_not_found(member_factory, association_factory):
    other = association_factory(slug="altra")
    member_factory(association=other, contact_email="maria@example.com")

    assert not Member.objects.for_contact(association_factory(slug="qui"), "maria@example.com").exists()


def test_an_inactive_member_is_not_offered(member_factory, association):
    member_factory(
        association=association, contact_email="maria@example.com", is_active=False
    )

    assert not Member.objects.for_contact(association, "maria@example.com").exists()
