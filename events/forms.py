"""
Formulaires de l'application « events ».

Toute la validation des données saisies se trouve ici : les vues se
contentent d'appeler form.is_valid().
"""

from django import forms
from django.utils import timezone

from .models import Categorie, Evenement


class EvenementForm(forms.ModelForm):
    """Création et modification d'un événement."""

    # Champ redéclaré pour imposer un minimum de 1 place (0 ou négatif = refusé).
    capacite = forms.IntegerField(
        label="Capacité d'accueil",
        min_value=1,
        help_text="Nombre maximum de participants.",
        error_messages={"min_value": "La capacité d'accueil doit être d'au moins 1 place."},
    )

    class Meta:
        model = Evenement
        fields = ["titre", "type_evenement", "categorie", "date", "lieu", "capacite", "description"]
        widgets = {
            # Sélecteur de date et d'heure natif du navigateur.
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_date(self):
        """Refuse une date passée (à la création, ou si la date est modifiée)."""
        date = self.cleaned_data["date"]
        est_creation = self.instance.pk is None
        if (est_creation or "date" in self.changed_data) and date < timezone.now():
            raise forms.ValidationError("La date de l'événement ne peut pas être dans le passé.")
        return date

    def clean_capacite(self):
        """En modification, la capacité ne peut pas descendre sous le nombre d'inscrits."""
        capacite = self.cleaned_data["capacite"]
        if self.instance.pk:
            nombre_inscrits = self.instance.inscriptions.count()
            if capacite < nombre_inscrits:
                raise forms.ValidationError(
                    f"Impossible : {nombre_inscrits} personnes sont déjà inscrites à cet événement."
                )
        return capacite


class CategorieForm(forms.ModelForm):
    """Création d'une catégorie (réservée aux utilisateurs qui ont la permission)."""

    class Meta:
        model = Categorie
        fields = ["nom", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_nom(self):
        """Refuse les doublons qui ne diffèrent que par les majuscules (« devops » / « DevOps »)."""
        nom = self.cleaned_data["nom"]
        if Categorie.objects.filter(nom__iexact=nom).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette catégorie existe déjà.")
        return nom


class FiltreEvenementsForm(forms.Form):
    """Valide les filtres reçus dans l'URL (?statut=...&categorie=...)."""

    STATUTS = [
        ("", "Tous"),
        ("a_venir", "À venir"),
        ("termines", "Terminés"),
        ("inscrits", "Mes inscriptions"),
    ]

    statut = forms.ChoiceField(choices=STATUTS, required=False)
    categorie = forms.ModelChoiceField(queryset=Categorie.objects.all(), required=False)
