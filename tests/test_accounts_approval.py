import pytest
from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from allauth.account.signals import email_confirmed, user_signed_up
from django.core import mail
from django.urls import reverse

from accounts.models import CustomUser
from accounts.notifications import deliver_account_approved, deliver_approval_request


@pytest.mark.django_db
def test_confirming_a_signup_deactivates_the_user_and_notifies_superusers(
    client, user_factory
):
    user_factory(email="root@example.com", is_superuser=True, is_staff=True)
    client.post(
        reverse("account_signup"),
        {"email": "new@example.com", "password1": "a-very-strong-pass-9"},
    )
    new_user = CustomUser.objects.get(email="new@example.com")
    assert new_user.is_active
    mail.outbox.clear()

    email_address = EmailAddress.objects.get(user=new_user)
    key = EmailConfirmationHMAC(email_address).key
    client.get(reverse("account_confirm_email", args=[key]))

    new_user.refresh_from_db()
    assert not new_user.is_active
    assert len(mail.outbox) == 1
    assert "root@example.com" in mail.outbox[0].to
    assert "new@example.com" in mail.outbox[0].body


@pytest.mark.django_db
def test_an_inactive_user_sees_the_pending_approval_page(client, user):
    user.is_active = False
    user.set_password("password")
    user.save()
    EmailAddress.objects.create(
        user=user, email=user.email, verified=True, primary=True
    )

    response = client.post(
        reverse("account_login"),
        {"login": user.email, "password": "password"},
        follow=True,
    )

    assert response.redirect_chain[-1][0] == reverse("account_inactive")


@pytest.mark.django_db
def test_approving_a_user_in_admin_activates_them_and_sends_an_email(
    staff_client, user_factory
):
    pending_user = user_factory(is_active=False)

    staff_client.post(
        reverse("admin:accounts_customuser_changelist"),
        {"action": "approve_users", "_selected_action": [pending_user.pk]},
    )

    pending_user.refresh_from_db()
    assert pending_user.is_active
    assert len(mail.outbox) == 1
    assert pending_user.email in mail.outbox[0].to


@pytest.mark.django_db
def test_a_pre_verified_signup_is_deactivated_immediately(user_factory):
    new_user = user_factory(is_active=True)
    EmailAddress.objects.create(
        user=new_user, email=new_user.email, verified=True, primary=True
    )

    user_signed_up.send(sender=new_user.__class__, request=None, user=new_user)

    new_user.refresh_from_db()
    assert not new_user.is_active


@pytest.mark.django_db
def test_confirming_email_for_an_already_inactive_user_is_a_noop(user_factory):
    inactive_user = user_factory(is_active=False)
    email_address = EmailAddress.objects.create(
        user=inactive_user, email=inactive_user.email, verified=True, primary=True
    )
    mail.outbox.clear()

    email_confirmed.send(
        sender=email_address.__class__, request=None, email_address=email_address
    )

    inactive_user.refresh_from_db()
    assert not inactive_user.is_active
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_delivering_approval_request_for_a_missing_user_is_a_noop():
    deliver_approval_request(999999)

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_delivering_approval_request_with_no_active_superusers_is_a_noop(
    user_factory,
):
    pending_user = user_factory()

    deliver_approval_request(pending_user.pk)

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_delivering_account_approved_for_a_missing_user_is_a_noop():
    deliver_account_approved(999999)

    assert len(mail.outbox) == 0
