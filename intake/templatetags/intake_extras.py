from django import template

register = template.Library()


@register.filter
def email_user(value):
    """The part before the @, for building an address a scraper can't read whole."""
    return value.split("@", 1)[0]


@register.filter
def email_domain(value):
    return value.split("@", 1)[-1]
