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
    path("evento/<slug:slug>/checkin/apri/", views.checkin_open, name="checkin-open"),
    path(
        "evento/<slug:slug>/checkin/chiudi/", views.checkin_close, name="checkin-close"
    ),
    path(
        "evento/<slug:slug>/soci/esporta/",
        views.export_members,
        name="export-members",
    ),
    path(
        "evento/<slug:slug>/checkin/<int:pk>/conferma/",
        views.checkin_confirm,
        name="checkin-confirm",
    ),
    path(
        "evento/<slug:slug>/checkin/<int:pk>/annulla/",
        views.checkin_undo,
        name="checkin-undo",
    ),
    path("evento/<slug:slug>/checkin/aggiungi/", views.checkin_add, name="checkin-add"),
    path(
        "evento/<slug:slug>/checkin/aggiungi/cf/",
        views.checkin_lookup,
        name="checkin-lookup",
    ),
    path("prenotazioni/", views.recover, name="recover"),
    path("prenotazioni/inviato/", views.recover_sent, name="recover-sent"),
    path("prenotazioni/<str:token>/", views.mine, name="mine"),
]
