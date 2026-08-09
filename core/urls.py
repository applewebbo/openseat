from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.urls import include, path
from pwa.views import manifest, offline, service_worker

from core.views import home

# The PWA endpoints must stay reachable anonymously, so they are declared here with
# login_not_required instead of including pwa.urls behind LoginRequiredMiddleware.
urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("serviceworker.js", login_not_required(service_worker), name="serviceworker"),
    path("manifest.json", login_not_required(manifest), name="manifest"),
    path("offline/", login_not_required(offline), name="offline"),
]

if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
