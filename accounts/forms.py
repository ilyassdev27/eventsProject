"""Formulaires de l'application « accounts »."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CreationCompteForm(UserCreationForm):
    """Création de compte : ajoute l'e-mail (obligatoire et unique), le prénom et le nom.

    UserCreationForm vérifie déjà le nom d'utilisateur, la solidité du mot de
    passe et que les deux mots de passe sont identiques.
    """

    email = forms.EmailField(label="Adresse e-mail")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte utilise déjà cette adresse e-mail.")
        return email
