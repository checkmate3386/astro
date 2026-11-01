from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from inscriptions.views import robots_txt, static_asset

urlpatterns = [
    path("robots.txt", robots_txt, name="robots"),
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
    # Les fichiers statiques passent par Django afin de recevoir aussi l'en-tête
    # X-Robots-Tag quand le serveur frontal ne les sert pas directement.
    re_path(
        r"^static/(?P<path>.*)$",
        static_asset,
        name="static-file",
    ),
    path("", include("inscriptions.urls")),
]
