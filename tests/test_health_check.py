import pytest
from django.db import connections
from django.urls import reverse

from core.views import _ConnectionClosingExecutor


@pytest.mark.django_db
def test_health_check_is_reachable_without_login(client):
    response = client.get(reverse("health-check"))

    assert response.status_code == 200
    assert response.json() == {"Database(alias='default')": "OK"}


def test_the_executor_closes_connections_opened_on_its_worker(monkeypatch):
    """A check that never runs on the main thread must not leave one behind."""
    closed = []
    monkeypatch.setattr(connections, "close_all", lambda: closed.append(True))

    with _ConnectionClosingExecutor(max_workers=1) as executor:
        executor.submit(lambda: None).result()

    assert closed == [True]
