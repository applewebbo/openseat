import asyncio
import re

from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from health_check.checks import Database
from health_check.views import HealthCheckView

from events.models import Event
from intake.models import Association

HEX_COLOUR = re.compile(r"^#[0-9A-Fa-f]{6}$")
FALLBACK_COLOURS = {
    "colour_primary": "#ED5C08",
    "colour_accent": "#528116",
    "colour_neutral": "#4C5057",
}


@login_not_required
def home(request):
    """The association's public page: who they are, and what can be booked.

    One installation serves one association, so the home page is that
    association's. Before there is one — a fresh install — the page says so
    instead of rendering an empty shell.
    """
    association = Association.current()
    if association is None:
        return render(request, "home-unconfigured.html", {"association": None})

    upcoming = list(Event.objects.filter(association=association).upcoming())
    can_manage_checkin = request.user.is_authenticated and request.user.has_perm(
        "events.change_event"
    )
    archive = (
        Event.objects.filter(association=association).past()
        if can_manage_checkin
        else []
    )
    return render(
        request,
        "home.html",
        {
            "association": association,
            # The soonest date carries the page; the others are dates, not news.
            "featured": upcoming[0] if upcoming else None,
            "upcoming": upcoming[1:],
            "archive": archive,
        },
    )


@login_not_required
@cache_control(max_age=300, public=True)
def theme_css(request, slug=None):
    """The association's colours as a stylesheet, so no page carries inline style.

    Named per association rather than served from one address: the form engine
    is meant to hold more than one, and a shared stylesheet would hand them all
    the same palette. Without a slug it answers for the installation's own
    association, which is how the admin — where no association names itself in
    the URL — reaches it. Values are re-checked here rather than trusted: a
    colour that reached the database without passing the field validator would
    otherwise be free text inside a stylesheet.
    """
    if slug is None:
        association = Association.current()
    else:
        association = Association.objects.filter(slug=slug).first()
    colours = dict(FALLBACK_COLOURS)
    for field, fallback in FALLBACK_COLOURS.items():
        value = getattr(association, field, "") or ""
        colours[field] = value if HEX_COLOUR.match(value) else fallback
    return render(
        request,
        "css/theme.css",
        {"association": colours},
        content_type="text/css",
    )


@method_decorator(login_not_required, name="dispatch")
class SiteHealthCheckView(HealthCheckView):
    """Whether the web process can reach the database, for Coolify's probe.

    Deliberately checks only the database: a broken migration or a crashed
    process are what a deploy probe needs to catch, and adding Redis/mail/
    storage would fail the probe on a dependency the web process itself
    doesn't need to serve a request. Always answers JSON: Coolify's health
    check path field takes a bare path, with no room for a `?format=json`
    query string to steer content negotiation.
    """

    checks = (Database,)

    async def get(self, request, *args, **kwargs):
        with self.get_executor() as executor:
            self.results = await asyncio.gather(
                *(check.get_result(executor) for check in self.get_checks())
            )
        has_errors = any(result.error for result in self.results)
        return self.render_to_response_json(500 if has_errors else 200)
