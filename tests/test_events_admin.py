import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.fixture
def spring_event(event_factory, association):
    """An event on a date with a weekday worth leaving out."""
    return event_factory(
        association=association,
        title="Festa di primavera",
        slug="festa-di-primavera",
        starts_at=timezone.make_aware(datetime.datetime(2026, 4, 20, 16, 0)),
    )


def _changelist(staff_client):
    response = staff_client.get(reverse("admin:events_event_changelist"))
    assert response.status_code == 200
    return response.content.decode()


def test_the_date_is_compact_and_carries_no_weekday(staff_client, spring_event):
    content = _changelist(staff_client)

    assert "20/04/2026 16:00" in content
    assert "Lunedì" not in content


def test_the_date_column_is_called_date(staff_client, spring_event):
    content = _changelist(staff_client)

    assert "column-starts_on" in content
    assert "Inizia il" not in content


def test_the_association_is_not_a_column(staff_client, spring_event):
    """One installation, one association: the same name on every row says nothing."""
    content = _changelist(staff_client)

    assert "field-association" not in content


def test_the_checklist_column_is_called_sent(staff_client, spring_event):
    content = _changelist(staff_client)

    assert "column-sent_on" in content
    assert "Lista inviata il" not in content


def test_the_dates_to_filter_by_sit_in_the_filter_card(staff_client, spring_event):
    """The month links belong with the other filters, not above the table."""
    content = _changelist(staff_client)

    card = content.split('id="changelist-filter"')[1].split("</search>")[0]
    assert "date-hierarchy" in card
    assert "Per data" in card
    assert "Filter by" not in content


def test_the_columns_are_named_in_italian(staff_client, spring_event):
    """The labels come from the project catalogue, so a stale .mo shows here."""
    content = _changelist(staff_client)

    assert ">Data</a>" in content
    assert ">Inviata</a>" in content
