"""
Vues de l'application « accounts » : connexion, déconnexion et création de compte.

La connexion et la déconnexion réutilisent les vues fournies par Django
(LoginView / LogoutView) : on ne réécrit pas ce que le framework fait déjà.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import CreationCompteForm


class ConnexionView(SuccessMessageMixin, LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True  # un utilisateur déjà connecté est redirigé
    success_message = "Bon retour parmi nous, %(username)s !"


class DeconnexionView(LogoutView):
    """Déconnexion : depuis Django 5, elle se fait uniquement en POST (protection CSRF)."""

    def post(self, request, *args, **kwargs):
        reponse = super().post(request, *args, **kwargs)
        messages.info(request, "Vous êtes maintenant déconnecté.")
        return reponse


def creer_compte(request):
    if request.user.is_authenticated:
        return redirect("events:liste")

    if request.method == "POST":
        form = CreationCompteForm(request.POST)
        if form.is_valid():
            utilisateur = form.save()
            login(request, utilisateur)  # connexion automatique après l'inscription
            messages.success(request, f"Bienvenue {utilisateur.username} ! Votre compte a été créé.")
            return redirect("events:liste")
    else:
        form = CreationCompteForm()

    contexte = {"form": form, "url_retour": reverse("events:liste")}
    return render(request, "accounts/creer_compte.html", contexte)
