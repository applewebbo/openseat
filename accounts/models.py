from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Manager for a user model keyed on email instead of username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("The email address is required"))
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("A superuser must have is_staff=True"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("A superuser must have is_superuser=True"))
        user = self._create_user(email, password, **extra_fields)
        # createsuperuser never goes through allauth's signup flow, so nothing
        # would otherwise verify the address — without this it is stuck behind
        # both mandatory email verification and the superuser-approval gate.
        EmailAddress.objects.update_or_create(
            user=user, email=user.email, defaults={"verified": True, "primary": True}
        )
        return user


class CustomUser(AbstractUser):
    """User identified by email; the username field is removed entirely."""

    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.email
