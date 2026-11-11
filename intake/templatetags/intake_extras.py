import re

from django import template

register = template.Library()

# Only these two plain-text substitutions are recognised in a custom section's
# rich text. A plain regex, not Django's template engine or str.format_map: no
# tag, no filter, no attribute lookup on the association object can ever run —
# an unknown or malformed `{...}` is left exactly as the admin typed it.
_CUSTOM_BODY_PLACEHOLDERS = re.compile(r"\{(association_name|membership_fee)\}")


@register.filter
def render_custom_body(value, association):
    """Substitute the whitelisted placeholders a custom section's text may use."""
    if not value:
        return value
    values = {
        "association_name": association.name,
        "membership_fee": association.membership_fee,
    }
    return _CUSTOM_BODY_PLACEHOLDERS.sub(lambda m: str(values[m.group(1)]), value)


@register.filter
def email_user(value):
    """The part before the @, for building an address a scraper can't read whole."""
    return value.split("@", 1)[0]


@register.filter
def email_domain(value):
    return value.split("@", 1)[-1]
