"""
Routage principal du projet.

Chaque application possède son propre fichier urls.py : ce fichier se
contente de les inclure.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("comptes/", include("accounts.urls")),
    path("", include("events.urls")),
]
