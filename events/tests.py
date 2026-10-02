"""
Tests de l'application « events ».

Lancer les tests : python manage.py test
"""

from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import EvenementForm
from .models import Categorie, Evenement, Inscription


def format_date(date):
    """Format envoyé par le champ <input type="datetime-local">."""
    return timezone.localtime(date).strftime("%Y-%m-%dT%H:%M")


class DonneesDeTest(TestCase):
    """Crée une catégorie, deux utilisateurs et un événement à venir de 2 places."""

    @classmethod
    def setUpTestData(cls):
        cls.categorie = Categorie.objects.create(nom="DevOps")
        cls.organisateur = User.objects.create_user("organisateur", password="motdepasse123")
        cls.autre = User.objects.create_user("autre", password="motdepasse123")
        cls.evenement = Evenement.objects.create(
            titre="Atelier Docker",
            date=timezone.now() + timedelta(days=7),
            lieu="Salle B12",
            capacite=2,
            categorie=cls.categorie,
            organisateur=cls.organisateur,
        )

    def donnees_formulaire(self, **modifications):
        donnees = {
            "titre": "Conférence IA",
            "type_evenement": "conference",
            "categorie": self.categorie.pk,
            "date": format_date(timezone.now() + timedelta(days=10)),
            "lieu": "Amphithéâtre A",
            "capacite": 50,
            "description": "",
        }
        donnees.update(modifications)
        return donnees


class EvenementFormTests(DonneesDeTest):
    def test_formulaire_valide(self):
        form = EvenementForm(data=self.donnees_formulaire())
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_passee_refusee(self):
        hier = format_date(timezone.now() - timedelta(days=1))
        form = EvenementForm(data=self.donnees_formulaire(date=hier))
        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)

    def test_capacite_negative_ou_nulle_refusee(self):
        for capacite in (-5, 0):
            form = EvenementForm(data=self.donnees_formulaire(capacite=capacite))
            self.assertFalse(form.is_valid())
            self.assertIn("capacite", form.errors)

    def test_capacite_inferieure_au_nombre_d_inscrits_refusee(self):
        Inscription.objects.create(utilisateur=self.autre, evenement=self.evenement)
        Inscription.objects.create(utilisateur=self.organisateur, evenement=self.evenement)
        form = EvenementForm(data=self.donnees_formulaire(capacite=1), instance=self.evenement)
        self.assertFalse(form.is_valid())
        self.assertIn("capacite", form.errors)

    def test_modifier_un_evenement_termine_sans_changer_sa_date(self):
        date_passee = (timezone.now() - timedelta(days=3)).replace(second=0, microsecond=0)
        ancien = Evenement.objects.create(
            titre="Ancien atelier", date=date_passee, lieu="Salle B12",
            capacite=10, categorie=self.categorie, organisateur=self.organisateur,
        )
        form = EvenementForm(data=self.donnees_formulaire(date=format_date(date_passee)), instance=ancien)
        self.assertTrue(form.is_valid(), form.errors)


class ContraintesBaseDeDonneesTests(DonneesDeTest):
    def test_capacite_nulle_refusee_par_la_base(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Evenement.objects.create(
                titre="Invalide", date=timezone.now(), lieu="Salle",
                capacite=0, categorie=self.categorie, organisateur=self.organisateur,
            )

    def test_double_inscription_refusee_par_la_base(self):
        Inscription.objects.create(utilisateur=self.autre, evenement=self.evenement)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Inscription.objects.create(utilisateur=self.autre, evenement=self.evenement)

    def test_nom_de_categorie_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categorie.objects.create(nom="DevOps")


class SecuriteTests(DonneesDeTest):
    def test_creation_exige_une_connexion(self):
        url = reverse("events:creer")
        reponse = self.client.get(url)
        self.assertRedirects(reponse, f"{reverse('accounts:login')}?next={url}")

    def test_createur_devient_organisateur(self):
        self.client.force_login(self.autre)
        reponse = self.client.post(reverse("events:creer"), self.donnees_formulaire())
        evenement = Evenement.objects.get(titre="Conférence IA")
        self.assertEqual(evenement.organisateur, self.autre)
        self.assertRedirects(reponse, evenement.get_absolute_url())

    def test_modification_interdite_a_un_autre_utilisateur(self):
        self.client.force_login(self.autre)
        for nom_url in ("events:modifier", "events:supprimer"):
            reponse = self.client.get(reverse(nom_url, args=[self.evenement.pk]))
            self.assertEqual(reponse.status_code, 403)

    def test_suppression_par_l_organisateur(self):
        self.client.force_login(self.organisateur)
        self.client.post(reverse("events:supprimer", args=[self.evenement.pk]))
        self.assertFalse(Evenement.objects.filter(pk=self.evenement.pk).exists())

    def test_creation_de_categorie_exige_la_permission(self):
        self.client.force_login(self.autre)
        url = reverse("events:creer_categorie")
        self.assertEqual(self.client.get(url).status_code, 403)

        self.autre.user_permissions.add(Permission.objects.get(codename="add_categorie"))
        self.assertEqual(self.client.get(url).status_code, 200)


class InscriptionTests(DonneesDeTest):
    def test_inscription_puis_doublon_ignore(self):
        self.client.force_login(self.autre)
        url = reverse("events:inscrire", args=[self.evenement.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(self.evenement.inscriptions.count(), 1)

    def test_inscription_impossible_en_get(self):
        self.client.force_login(self.autre)
        reponse = self.client.get(reverse("events:inscrire", args=[self.evenement.pk]))
        self.assertEqual(reponse.status_code, 405)

    def test_evenement_complet(self):
        troisieme = User.objects.create_user("troisieme", password="motdepasse123")
        Inscription.objects.create(utilisateur=self.autre, evenement=self.evenement)
        Inscription.objects.create(utilisateur=self.organisateur, evenement=self.evenement)
        self.client.force_login(troisieme)
        self.client.post(reverse("events:inscrire", args=[self.evenement.pk]))
        self.assertFalse(Inscription.objects.filter(utilisateur=troisieme).exists())

    def test_desinscription(self):
        Inscription.objects.create(utilisateur=self.autre, evenement=self.evenement)
        self.client.force_login(self.autre)
        self.client.post(reverse("events:desinscrire", args=[self.evenement.pk]))
        self.assertEqual(self.evenement.inscriptions.count(), 0)


class PagesTests(DonneesDeTest):
    def test_liste_et_statut(self):
        reponse = self.client.get(reverse("events:liste"))
        self.assertContains(reponse, "Atelier Docker")
        self.assertContains(reponse, "À venir")

    def test_filtre_mes_inscriptions(self):
        Evenement.objects.create(
            titre="Autre événement", date=timezone.now() + timedelta(days=3), lieu="En ligne",
            capacite=5, categorie=self.categorie, organisateur=self.organisateur,
        )
        Inscription.objects.create(utilisateur=self.autre, evenement=self.evenement)
        self.client.force_login(self.autre)
        reponse = self.client.get(reverse("events:liste"), {"statut": "inscrits"})
        self.assertEqual(list(reponse.context["evenements"]), [self.evenement])
        self.assertContains(reponse, "Inscrit")

    def test_filtre_invalide_ignore(self):
        reponse = self.client.get(reverse("events:liste"), {"categorie": "abc", "statut": "xyz"})
        self.assertEqual(reponse.status_code, 200)

    def test_detail(self):
        reponse = self.client.get(self.evenement.get_absolute_url())
        self.assertContains(reponse, "Atelier Docker")
        self.assertContains(reponse, "Se connecter pour s'inscrire")

    def test_tableau_de_bord(self):
        Inscription.objects.create(utilisateur=self.autre, evenement=self.evenement)
        self.client.force_login(self.autre)
        reponse = self.client.get(reverse("events:tableau_de_bord"))
        self.assertEqual(list(reponse.context["prochains"]), [self.evenement])
