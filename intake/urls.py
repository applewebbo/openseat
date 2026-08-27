from django.urls import path

from intake import views

app_name = "intake"

# The two named request routes are declared before the catch-all step route, or
# "submit" and "done" would be read as section names.
urlpatterns = [
    path("comuni/", views.comuni_options, name="comuni-options"),
    path("modulo/<slug:slug>/", views.landing, name="landing"),
    path("modulo/<slug:slug>/start/", views.begin, name="begin"),
    path("richiesta/<uuid:token>/save/", views.save, name="save"),
    path("richiesta/<uuid:token>/saved/", views.saved, name="saved"),
    path("richiesta/<uuid:token>/review/", views.review, name="review"),
    path("richiesta/<uuid:token>/submit/", views.submit, name="submit"),
    path("richiesta/<uuid:token>/done/", views.done, name="done"),
    path("richiesta/<uuid:token>/<slug:step>/", views.step, name="step"),
    path("consenso/<uuid:token>/", views.second_parent, name="second-parent"),
]
