import pytest
from django.core.management import call_command
from django.utils import timezone

from events.models import Booking, Event
from intake.models import Association, PublicForm, SectionKey
from members.models import Member


@pytest.fixture
def seeded():
    call_command("seed_demo", verbosity=0)
    return Association.objects.get()


@pytest.mark.django_db
def test_it_creates_an_association_with_a_home_page(seeded):
    assert seeded.home_title
    assert "<p>" in seeded.home_description


@pytest.mark.django_db
def test_the_form_gets_the_whole_section_catalogue(seeded):
    public_form = PublicForm.objects.get()

    assert public_form.association == seeded
    assert set(public_form.sections.values_list("key", flat=True)) == set(
        SectionKey.values
    )


@pytest.mark.django_db
def test_there_is_always_a_next_date_and_an_archive(seeded):
    assert Event.objects.upcoming().exists()
    assert Event.objects.past().exists()
    assert Event.objects.filter(starts_at__lt=timezone.now()).count() == 3


@pytest.mark.django_db
def test_events_book_through_the_seeded_form(seeded):
    public_form = PublicForm.objects.get()

    assert Event.objects.filter(form=public_form).count() == Event.objects.count()


@pytest.mark.django_db
def test_an_existing_association_is_filled_in_not_duplicated(association):
    """The admin allows one association; the command must not make a second."""
    call_command("seed_demo", verbosity=0)

    assert Association.objects.count() == 1
    association.refresh_from_db()
    assert association.home_title
    assert Event.objects.filter(association=association).count() == 5


@pytest.mark.django_db
def test_text_somebody_already_wrote_is_left_alone(association):
    association.home_title = "Il nostro titolo"
    association.save()

    call_command("seed_demo", verbosity=0)

    association.refresh_from_db()
    assert association.home_title == "Il nostro titolo"


@pytest.mark.django_db
def test_running_it_twice_changes_nothing(seeded):
    member_count = Member.objects.count()
    booking_count = Booking.objects.count()

    call_command("seed_demo", verbosity=0)

    assert Association.objects.count() == 1
    assert PublicForm.objects.count() == 1
    assert Event.objects.count() == 5
    # The sections are installed once, not stacked on the second run.
    assert PublicForm.objects.get().sections.count() == len(SectionKey.values)
    assert Member.objects.count() == member_count
    assert Booking.objects.count() == booking_count


@pytest.mark.django_db
def test_every_event_gets_a_realistic_roster(seeded):
    for event in Event.objects.all():
        assert 10 <= event.bookings.active().count() <= 15


@pytest.mark.django_db
def test_the_roster_has_a_mix_of_confirmed_and_pending(seeded):
    event = Event.objects.first()

    assert event.bookings.filter(confirmed_on__isnull=False).exists()
    assert event.bookings.unconfirmed().exists()


@pytest.mark.django_db
def test_confirmed_bookings_carry_a_fee(seeded):
    booking = Booking.objects.filter(confirmed_on__isnull=False).first()

    assert booking.fee_amount is not None
    assert booking.fee_method == "cash"


@pytest.mark.django_db
def test_members_are_shared_across_events_not_duplicated_per_event(seeded):
    assert (
        Member.objects.filter(submission__isnull=False).count()
        < Booking.objects.count()
    )


@pytest.mark.django_db
def test_it_seeds_a_realistic_register_for_export(seeded):
    standalone = Member.objects.filter(submission__isnull=True)

    assert standalone.count() == 50
    assert standalone.exclude(tax_code="").count() < standalone.count()
    assert standalone.filter(ratified_on__isnull=True).exists()
    assert standalone.filter(ratified_on__isnull=False).exists()
    assert standalone.values_list("joined_on", flat=True).distinct().count() > 1
