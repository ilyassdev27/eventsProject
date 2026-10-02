"""
Tests de l'application « accounts ».

Lancer les tests : python manage.py test
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

MOT_DE_PASSE = "UnMotDePasseSolide!2026"


class CreationCompteTests(TestCase):
    def donnees(self, **modifications):
        donnees = {
            "username": "nouveau",
            "first_name": "",
            "last_name": "",
            "email": "nouveau@example.com",
            "password1": MOT_DE_PASSE,
            "password2": MOT_DE_PASSE,
        }
        donnees.update(modifications)
        return donnees

    def test_creation_de_compte_puis_connexion_automatique(self):
        reponse = self.client.post(reverse("accounts:signup"), self.donnees())
        self.assertRedirects(reponse, reverse("events:liste"))
        utilisateur = User.objects.get(username="nouveau")
        self.assertEqual(int(self.client.session["_auth_user_id"]), utilisateur.pk)

    def test_email_deja_utilise(self):
        User.objects.create_user("ancien", email="nouveau@example.com", password=MOT_DE_PASSE)
        reponse = self.client.post(reverse("accounts:signup"), self.donnees(email="NOUVEAU@example.com"))
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("email", reponse.context["form"].errors)

    def test_mots_de_passe_differents(self):
        reponse = self.client.post(reverse("accounts:signup"), self.donnees(password2="autre-chose"))
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(User.objects.filter(username="nouveau").exists())


class ConnexionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.utilisateur = User.objects.create_user("demo", password=MOT_DE_PASSE)

    def test_connexion(self):
        reponse = self.client.post(reverse("accounts:login"), {"username": "demo", "password": MOT_DE_PASSE})
        self.assertRedirects(reponse, reverse("events:liste"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_connexion_mauvais_mot_de_passe(self):
        reponse = self.client.post(reverse("accounts:login"), {"username": "demo", "password": "faux"})
        self.assertEqual(reponse.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_connexion_redirige_vers_next(self):
        url_suivante = reverse("events:creer")
        reponse = self.client.post(
            reverse("accounts:login"),
            {"username": "demo", "password": MOT_DE_PASSE, "next": url_suivante},
        )
        self.assertRedirects(reponse, url_suivante)

    def test_deconnexion_en_post(self):
        self.client.force_login(self.utilisateur)
        reponse = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(reponse, reverse("events:liste"))
        self.assertNotIn("_auth_user_id", self.client.session)
