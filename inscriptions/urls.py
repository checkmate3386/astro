from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("soirees/<slug:slug>/", views.event_detail, name="event-detail"),
]
