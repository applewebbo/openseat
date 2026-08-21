from django.urls import path

from events import views

app_name = "events"

urlpatterns = [
    path("evento/<slug:slug>/", views.landing, name="landing"),
    path("evento/<slug:slug>/identify/", views.identify, name="identify"),
    path("evento/<slug:slug>/book/", views.book, name="book"),
    path("evento/<slug:slug>/booked/", views.booked, name="booked"),
    path("evento/<slug:slug>/cancel/<int:pk>/", views.cancel, name="cancel"),
    path("evento/<slug:slug>/edit/<int:pk>/", views.edit, name="edit"),
    path("evento/<slug:slug>/prenotazione/<str:token>/", views.manage, name="manage"),
    path("evento/<slug:slug>/join/", views.join, name="join"),
]
