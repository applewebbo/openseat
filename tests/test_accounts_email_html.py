import pytest
from django.core import mail
from django.core.cache import cache
from django.urls import reverse


@pytest.mark.django_db
def test_password_reset_email_carries_an_html_alternative(client, user):
    cache.clear()
    client.post(reverse("account_reset_password"), {"email": user.email})

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert len(message.alternatives) == 1
    html_body, mimetype = message.alternatives[0]
    assert mimetype == "text/html"
    assert "<!DOCTYPE html>" in html_body


@pytest.mark.django_db
def test_signup_confirmation_email_carries_an_html_alternative(client):
    cache.clear()
    client.post(
        reverse("account_signup"),
        {"email": "new@example.com", "password1": "a-very-strong-pass-9"},
    )

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert len(message.alternatives) == 1
    html_body, mimetype = message.alternatives[0]
    assert mimetype == "text/html"
    assert "<!DOCTYPE html>" in html_body
