"""Cleaning for the little HTML the admin is allowed to author."""

import nh3

# The home page description is written in the admin by a volunteer, with an
# editor whose toolbar offers exactly these. Anything else — a paste from a word
# processor, a tag typed into the source, a stray handler — is dropped rather
# than trusted, so the public page can never be made to run somebody's script.
ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "u",
    "ul",
    "ol",
    "li",
    "a",
    "h2",
    "h3",
    "blockquote",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}


def clean_rich_text(value):
    """Return the value with everything outside the allowlist removed."""
    if not value:
        return value
    return nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel="noopener noreferrer",
    )
