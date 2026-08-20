import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from PIL import Image

from events.images import SQUARE_SIDE

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


def wide_upload(name="asini.jpg", size=(1600, 900), colour="#8899aa"):
    buffer = io.BytesIO()
    Image.new("RGB", size, colour).save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


def opened(field):
    with field.open("rb") as handle:
        return Image.open(io.BytesIO(handle.read()))


def test_a_wide_picture_gets_a_square_one(event):
    event.image = wide_upload()
    event.save()

    event.refresh_from_db()
    assert event.image_square
    assert opened(event.image_square).size == (SQUARE_SIDE, SQUARE_SIDE)


def test_the_crop_leans_towards_the_top_of_the_frame(event):
    """Heads sit above the middle, so the cut starts a quarter of the way down
    the spare height rather than halfway: on a 400x1000 picture, at y=150."""
    source = Image.new("RGB", (400, 1000), "#ffffff")
    source.paste(Image.new("RGB", (400, 40), "#000000"), (0, 150))
    buffer = io.BytesIO()
    source.save(buffer, format="JPEG")
    event.image = SimpleUploadedFile("tall.jpg", buffer.getvalue(), "image/jpeg")
    event.save()

    square = opened(event.image_square).convert("RGB")
    assert square.getpixel((SQUARE_SIDE // 2, 10))[0] < 40
    assert square.getpixel((SQUARE_SIDE // 2, SQUARE_SIDE // 2))[0] > 200


def test_the_square_is_not_made_again_on_every_save(event):
    event.image = wide_upload()
    event.save()
    first = event.image_square.name

    event.title = "Un altro titolo"
    event.save()

    assert event.image_square.name == first


def test_replacing_the_picture_replaces_the_square(event):
    event.image = wide_upload()
    event.save()
    first = event.image_square.name

    event.image = wide_upload(name="altra.jpg")
    event.save()

    assert event.image_square.name != first


def test_dropping_the_picture_drops_the_square(event):
    event.image = wide_upload()
    event.save()

    event.image = None
    event.save()

    event.refresh_from_db()
    assert not event.image_square


class TestTheDefaultPicture:
    """The bundled fallback is cut by the same rule as an uploaded one, so the
    two never disagree about what a square picture looks like."""

    def test_the_square_default_is_cut_from_the_wide_one(self, tmp_path):
        wide = tmp_path / "wide.jpg"
        Image.new("RGB", (1600, 900), "#8899aa").save(wide)
        square = tmp_path / "square.jpg"

        call_command("default_event_square", wide=str(wide), square=str(square))

        with Image.open(square) as cut:
            assert cut.size == (SQUARE_SIDE, SQUARE_SIDE)

    def test_a_missing_wide_default_says_so(self, tmp_path):
        with pytest.raises(CommandError, match="no wide default picture"):
            call_command(
                "default_event_square",
                wide=str(tmp_path / "nothing.jpg"),
                square=str(tmp_path / "square.jpg"),
            )


def test_an_event_without_a_picture_shows_the_default_artwork(event):
    assert "event-default" in event.wide_url
    assert "event-default" in event.square_url


def test_an_uploaded_picture_is_the_one_shown(event):
    event.image = wide_upload()
    event.save()

    assert event.wide_url == event.image.url
    assert event.square_url == event.image_square.url
