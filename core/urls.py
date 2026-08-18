from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.urls import include, path, re_path
from pwa.views import manifest, offline, service_worker

from core.views import home

# The PWA endpoints must stay reachable anonymously, so they are declared here with
# login_not_required instead of including pwa.urls behind LoginRequiredMiddleware.
urlpatterns = [
    path("", home, name="home"),
    path("", include("intake.urls")),
    path("", include("events.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("serviceworker.js", login_not_required(service_worker), name="serviceworker"),
    path("manifest.json", login_not_required(manifest), name="manifest"),
    path("offline/", login_not_required(offline), name="offline"),
]

if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
    # LoginRequiredMiddleware guards every route, media included, so the dev
    # media view is opted out explicitly: the public form shows the association
    # logo to people who have no account by design.
    urlpatterns += [
        re_path(
            route.pattern.regex.pattern,
            login_not_required(route.callback),
            kwargs=route.default_args,
        )
        for route in static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    ]
