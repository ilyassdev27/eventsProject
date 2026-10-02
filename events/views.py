"""
Vues de l'application « events ».

Chaque vue reste courte : elle récupère les données, délègue la validation
aux formulaires (forms.py) et renvoie un template.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CategorieForm, EvenementForm, FiltreEvenementsForm
from .models import Categorie, Evenement, Inscription

# --- Fonctions utilitaires ---------------------------------------------------


def _ids_evenements_inscrits(utilisateur):
    """Ensemble des identifiants des événements auxquels l'utilisateur est inscrit."""
    if not utilisateur.is_authenticated:
        return set()
    return set(utilisateur.inscriptions.values_list("evenement_id", flat=True))


def _get_evenement_modifiable(request, pk):
    """Renvoie l'événement si l'utilisateur a le droit de le modifier, sinon erreur 403."""
    evenement = get_object_or_404(Evenement, pk=pk)
    if not evenement.peut_etre_modifie_par(request.user):
        raise PermissionDenied
    return evenement


# --- Consultation (accessible à tous) ---------------------------------------


def liste_evenements(request):
    """Page d'accueil : liste des événements, filtrable par statut et par catégorie."""
    filtre = FiltreEvenementsForm(request.GET)
    statut, categorie = "", None
    if filtre.is_valid():
        statut = filtre.cleaned_data["statut"]
        categorie = filtre.cleaned_data["categorie"]

    inscrits_ids = _ids_evenements_inscrits(request.user)
    evenements = Evenement.objects.select_related("categorie").avec_nombre_inscrits()

    if categorie:
        evenements = evenements.filter(categorie=categorie)
    if statut == "a_venir":
        evenements = evenements.a_venir()
    elif statut == "termines":
        evenements = evenements.termines()
    elif statut == "inscrits":
        evenements = evenements.filter(pk__in=inscrits_ids)

    # L'onglet « Mes inscriptions » n'a de sens que pour un utilisateur connecté.
    statuts = [s for s in FiltreEvenementsForm.STATUTS if s[0] != "inscrits" or request.user.is_authenticated]

    contexte = {
        "evenements": evenements,
        "categories": Categorie.objects.annotate(nb_evenements=Count("evenements")),
        "statuts": statuts,
        "statut_actif": statut,
        "categorie_active": categorie,
        "inscrits_ids": inscrits_ids,
    }
    return render(request, "events/liste_evenements.html", contexte)


def detail_evenement(request, pk):
    """Fiche détaillée d'un événement."""
    evenement = get_object_or_404(
        Evenement.objects.select_related("categorie", "organisateur").avec_nombre_inscrits(),
        pk=pk,
    )
    inscrits_ids = _ids_evenements_inscrits(request.user)
    peut_modifier = evenement.peut_etre_modifie_par(request.user)

    contexte = {
        "evenement": evenement,
        "inscrits_ids": inscrits_ids,
        "est_inscrit": evenement.pk in inscrits_ids,
        "peut_modifier": peut_modifier,
        # La liste des participants n'est visible que par l'organisateur.
        "participants": evenement.inscriptions.select_related("utilisateur") if peut_modifier else None,
    }
    return render(request, "events/detail_evenement.html", contexte)


# --- Gestion des événements (utilisateur connecté) --------------------------


@login_required
def creer_evenement(request):
    if request.method == "POST":
        form = EvenementForm(request.POST)
        if form.is_valid():
            evenement = form.save(commit=False)
            evenement.organisateur = request.user  # le créateur devient l'organisateur
            evenement.save()
            messages.success(request, f"L'événement « {evenement.titre} » a été créé.")
            return redirect(evenement)
    else:
        form = EvenementForm()

    contexte = {
        "form": form,
        "titre_page": "Nouvel événement",
        "texte_bouton": "Créer l'événement",
        "url_retour": reverse("events:liste"),
    }
    return render(request, "formulaire.html", contexte)


@login_required
def modifier_evenement(request, pk):
    evenement = _get_evenement_modifiable(request, pk)
    if request.method == "POST":
        form = EvenementForm(request.POST, instance=evenement)
        if form.is_valid():
            form.save()
            messages.success(request, "Les modifications ont été enregistrées.")
            return redirect(evenement)
    else:
        form = EvenementForm(instance=evenement)

    contexte = {
        "form": form,
        "titre_page": f"Modifier « {evenement.titre} »",
        "texte_bouton": "Enregistrer",
        "url_retour": evenement.get_absolute_url(),
    }
    return render(request, "formulaire.html", contexte)


@login_required
def supprimer_evenement(request, pk):
    evenement = _get_evenement_modifiable(request, pk)
    if request.method == "POST":
        evenement.delete()
        messages.success(request, f"L'événement « {evenement.titre} » a été supprimé.")
        return redirect("events:liste")
    return render(request, "events/confirmer_suppression.html", {"evenement": evenement})


# --- Inscriptions ------------------------------------------------------------


@login_required
@require_POST
def inscrire(request, pk):
    evenement = get_object_or_404(Evenement, pk=pk)
    if evenement.est_termine:
        messages.error(request, "Cet événement est terminé : les inscriptions sont fermées.")
    elif evenement.est_complet:
        messages.error(request, "Désolé, cet événement est complet.")
    else:
        # get_or_create évite les doublons (en plus de la contrainte unique en base).
        _, cree = Inscription.objects.get_or_create(utilisateur=request.user, evenement=evenement)
        if cree:
            messages.success(request, "Votre inscription est confirmée.")
        else:
            messages.info(request, "Vous êtes déjà inscrit à cet événement.")
    return redirect(evenement)


@login_required
@require_POST
def desinscrire(request, pk):
    evenement = get_object_or_404(Evenement, pk=pk)
    if evenement.est_termine:
        messages.error(request, "Impossible de se désinscrire d'un événement terminé.")
    else:
        supprimees, _ = Inscription.objects.filter(utilisateur=request.user, evenement=evenement).delete()
        if supprimees:
            messages.success(request, "Votre inscription a été annulée.")
    return redirect(evenement)


@login_required
def tableau_de_bord(request):
    """Espace personnel : suivi des inscriptions et des événements organisés."""
    evenements = Evenement.objects.select_related("categorie").avec_nombre_inscrits()
    inscrits_ids = _ids_evenements_inscrits(request.user)
    mes_inscriptions = evenements.filter(pk__in=inscrits_ids)

    contexte = {
        "prochains": mes_inscriptions.a_venir(),
        "historique": mes_inscriptions.termines(),
        "organises": evenements.filter(organisateur=request.user),
        "inscrits_ids": inscrits_ids,
    }
    return render(request, "events/tableau_de_bord.html", contexte)


# --- Catégories (permission Django requise) ---------------------------------


@login_required
@permission_required("events.add_categorie", raise_exception=True)
def creer_categorie(request):
    if request.method == "POST":
        form = CategorieForm(request.POST)
        if form.is_valid():
            categorie = form.save()
            messages.success(request, f"La catégorie « {categorie.nom} » a été créée.")
            return redirect(f"{reverse('events:liste')}?categorie={categorie.pk}")
    else:
        form = CategorieForm()

    contexte = {
        "form": form,
        "titre_page": "Nouvelle catégorie",
        "texte_bouton": "Créer la catégorie",
        "url_retour": reverse("events:liste"),
    }
    return render(request, "formulaire.html", contexte)
