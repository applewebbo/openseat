from django.urls import path

from intake import views

app_name = "intake"

# The two named request routes are declared before the catch-all step route, or
# "submit" and "done" would be read as section names.
urlpatterns = [
    path("m/<slug:slug>/", views.landing, name="landing"),
    path("m/<slug:slug>/start/", views.begin, name="begin"),
    path("r/<uuid:token>/save/", views.save, name="save"),
    path("r/<uuid:token>/saved/", views.saved, name="saved"),
    path("r/<uuid:token>/review/", views.review, name="review"),
    path("r/<uuid:token>/submit/", views.submit, name="submit"),
    path("r/<uuid:token>/done/", views.done, name="done"),
    path("r/<uuid:token>/<slug:step>/", views.step, name="step"),
    path("c/<uuid:token>/", views.second_parent, name="second-parent"),
]
