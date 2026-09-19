import pytest
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives

from core.mail import LOGO_CONTENT_ID, attach_logo, from_header

pytestmark = pytest.mark.django_db


def test_the_from_header_names_the_association(association, settings):
    settings.DEFAULT_FROM_EMAIL = "noreply@example.com"
    association.name = "Circolo Aurora"

    assert from_header(association) == "Circolo Aurora <noreply@example.com>"


def test_no_logo_attaches_nothing(association):
    message = EmailMultiAlternatives()

    attach_logo(message, association)

    assert message.attachments == []


def test_a_none_association_is_a_noop():
    message = EmailMultiAlternatives()

    attach_logo(message, None)

    assert message.attachments == []


def test_the_logo_is_attached_inline(association):
    association.logo.save("logo.png", ContentFile(b"fake-png-bytes"), save=True)
    message = EmailMultiAlternatives()

    attach_logo(message, association)

    (attachment,) = message.attachments
    assert attachment["Content-ID"] == f"<{LOGO_CONTENT_ID}>"
    assert attachment["Content-Disposition"].startswith("inline")
    assert attachment.get_content_type() == "image/png"
