import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model

from accounts.models import CustomUser

User = get_user_model()


@pytest.mark.django_db
def test_create_user_normalises_email():
    user = User.objects.create_user(email="Person@EXAMPLE.COM", password="pwd")

    assert user.email == "Person@example.com"
    assert user.check_password("pwd")
    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_create_user_without_email_is_rejected(english):
    with pytest.raises(ValueError, match="email address is required"):
        User.objects.create_user(email="", password="pwd")


@pytest.mark.django_db
def test_create_superuser():
    user = User.objects.create_superuser(email="root@example.com", password="pwd")

    assert user.is_staff
    assert user.is_superuser


@pytest.mark.django_db
def test_create_superuser_requires_is_staff(english):
    with pytest.raises(ValueError, match="is_staff=True"):
        User.objects.create_superuser(
            email="root@example.com", password="pwd", is_staff=False
        )


@pytest.mark.django_db
def test_create_superuser_requires_is_superuser(english):
    with pytest.raises(ValueError, match="is_superuser=True"):
        User.objects.create_superuser(
            email="root@example.com", password="pwd", is_superuser=False
        )


@pytest.mark.django_db
def test_str_is_the_email(user):
    assert str(user) == user.email


def test_user_has_no_username_field():
    assert User.USERNAME_FIELD == "email"
    assert User.REQUIRED_FIELDS == []


def test_custom_user_is_registered_in_admin():
    assert admin.site.is_registered(CustomUser)
