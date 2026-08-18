from django.urls import path

from events import views

app_name = "events"

urlpatterns = [
    path("e/<slug:slug>/", views.landing, name="landing"),
    path("e/<slug:slug>/identify/", views.identify, name="identify"),
    path("e/<slug:slug>/book/", views.book, name="book"),
    path("e/<slug:slug>/booked/", views.booked, name="booked"),
    path("e/<slug:slug>/join/", views.join, name="join"),
]
