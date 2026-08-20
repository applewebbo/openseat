"""The square version of an event picture, derived from the wide one."""

import io
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

SQUARE_SIDE = 800
QUALITY = 85

# Where the crop sits vertically, as a fraction of the room left over. A photo
# of children and animals carries its subject above the middle, so a centred
# crop tends to cut heads off; a quarter down keeps them.
TOP_BIAS = 0.25


def square_name(name):
    return f"square/{Path(name).stem}.jpg"


def square_bytes(handle):
    """A square JPEG cut out of an open picture."""
    source = Image.open(io.BytesIO(handle.read()))
    source = ImageOps.exif_transpose(source).convert("RGB")

    side = min(source.width, source.height)
    left = round((source.width - side) / 2)
    top = round((source.height - side) * TOP_BIAS)
    square = source.crop((left, top, left + side, top + side))
    square = square.resize((SQUARE_SIDE, SQUARE_SIDE), Image.LANCZOS)

    buffer = io.BytesIO()
    square.save(buffer, format="JPEG", quality=QUALITY, optimize=True)
    return buffer.getvalue()


def square_from(image_field):
    """The same cut, ready to hand to an ImageField."""
    with image_field.open("rb") as handle:
        return ContentFile(square_bytes(handle))
