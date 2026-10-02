"""Routes de l'application « accounts »."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("connexion/", views.ConnexionView.as_view(), name="login"),
    path("deconnexion/", views.DeconnexionView.as_view(), name="logout"),
    path("creer-compte/", views.creer_compte, name="signup"),
]
