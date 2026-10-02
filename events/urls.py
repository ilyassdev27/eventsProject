"""Routes de l'application « events »."""

from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.liste_evenements, name="liste"),
    path("tableau-de-bord/", views.tableau_de_bord, name="tableau_de_bord"),
    path("evenements/nouveau/", views.creer_evenement, name="creer"),
    path("evenements/<int:pk>/", views.detail_evenement, name="detail"),
    path("evenements/<int:pk>/modifier/", views.modifier_evenement, name="modifier"),
    path("evenements/<int:pk>/supprimer/", views.supprimer_evenement, name="supprimer"),
    path("evenements/<int:pk>/inscription/", views.inscrire, name="inscrire"),
    path("evenements/<int:pk>/desinscription/", views.desinscrire, name="desinscrire"),
    path("categories/nouvelle/", views.creer_categorie, name="creer_categorie"),
]
