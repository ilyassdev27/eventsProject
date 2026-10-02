"""
Commande : python manage.py charger_demo

Remplit la base avec des données de démonstration : catégories, utilisateurs,
événements à venir et terminés, inscriptions. Les dates sont calculées par
rapport à aujourd'hui, pour que la démo ait toujours des événements « À venir »
et « Terminés ». La commande peut être relancée sans créer de doublons.
"""

from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from events.models import Categorie, Evenement, Inscription

# Comptes de démonstration : (nom d'utilisateur, mot de passe, administrateur ?)
UTILISATEURS = [
    ("admin", "admin12345", True),
    ("demo", "demo12345", False),
    ("sara", "demo12345", False),
]

CATEGORIES = {
    "IA": ("Intelligence Artificielle", "Machine learning, IA générative, vision par ordinateur."),
    "DEVOPS": ("DevOps", "Conteneurs, intégration et déploiement continus, automatisation."),
    "SECU": ("Cybersécurité", "Sécurité des applications, des réseaux et des données."),
    "CLOUD": ("Cloud Computing", "Services cloud, architecture et certifications."),
    "WEB": ("Développement Web", "Frameworks, API et bonnes pratiques du web."),
}

Type = Evenement.TypeEvenement

# (titre, type, catégorie, jours par rapport à aujourd'hui, heure, lieu, capacité, organisateur, description)
EVENEMENTS = [
    (
        "Introduction à l'IA générative et aux LLM", Type.CONFERENCE, "IA", 6, 14,
        "Casablanca – Amphithéâtre A", 120, "admin",
        "Comprendre le fonctionnement des grands modèles de langage, leurs usages "
        "concrets en entreprise et leurs limites.",
    ),
    (
        "Django pour débutants : votre premier projet", Type.ATELIER, "WEB", 4, 14,
        "Salle C3", 2, "admin",
        "Atelier pratique : modèles, vues, templates et formulaires en construisant "
        "une petite application pas à pas.",
    ),
    (
        "Atelier Docker : conteneuriser une application Django", Type.ATELIER, "DEVOPS", 9, 10,
        "Salle informatique B12", 25, "sara",
        "Écrire un Dockerfile, utiliser docker compose et préparer une application "
        "pour le déploiement.",
    ),
    (
        "Sécuriser une application web : l'OWASP Top 10", Type.CONFERENCE, "SECU", 13, 15,
        "En ligne", 200, "admin",
        "Tour d'horizon des vulnérabilités web les plus courantes et des bonnes "
        "pratiques pour s'en protéger.",
    ),
    (
        "Pipeline CI/CD avec GitHub Actions", Type.ATELIER, "DEVOPS", 20, 9,
        "Salle informatique B12", 20, "demo",
        "Automatiser les tests et le déploiement d'un projet à chaque push.",
    ),
    (
        "Préparation à la certification AWS Cloud Practitioner", Type.CERTIFICATION, "CLOUD", 28, 9,
        "Rabat – Centre de formation", 30, "sara",
        "Révision des notions clés du cloud et examen blanc dans les conditions réelles.",
    ),
    (
        "Hackathon IA : vision par ordinateur", Type.ATELIER, "IA", -18, 9,
        "Casablanca – Espace coworking", 40, "admin",
        "Une journée pour construire un prototype de reconnaissance d'images en équipe.",
    ),
    (
        "Capture The Flag pour débutants", Type.ATELIER, "SECU", -9, 18,
        "Salle informatique B12", 30, "demo",
        "Initiation à la sécurité offensive à travers des défis progressifs.",
    ),
    (
        "Initiation à Kubernetes", Type.ATELIER, "CLOUD", -35, 14,
        "En ligne", 50, "sara",
        "Pods, deployments et services : les bases pour orchestrer des conteneurs.",
    ),
]

# (utilisateur, titre de l'événement)
INSCRIPTIONS = [
    ("demo", "Introduction à l'IA générative et aux LLM"),
    ("demo", "Django pour débutants : votre premier projet"),
    ("sara", "Django pour débutants : votre premier projet"),
    ("sara", "Sécuriser une application web : l'OWASP Top 10"),
    ("demo", "Hackathon IA : vision par ordinateur"),
    ("demo", "Initiation à Kubernetes"),
    ("sara", "Capture The Flag pour débutants"),
]


def date_relative(jours, heure):
    """Date située à `jours` jours d'aujourd'hui (négatif = passé), à l'heure indiquée."""
    jour = timezone.localdate() + timedelta(days=jours)
    return timezone.make_aware(datetime.combine(jour, time(hour=heure)))


class Command(BaseCommand):
    help = "Charge des données de démonstration (catégories, utilisateurs, événements, inscriptions)."

    @transaction.atomic
    def handle(self, *args, **options):
        utilisateurs = {}
        for nom, mot_de_passe, est_admin in UTILISATEURS:
            utilisateur, cree = User.objects.get_or_create(
                username=nom,
                defaults={"email": f"{nom}@example.com", "is_staff": est_admin, "is_superuser": est_admin},
            )
            if cree:
                utilisateur.set_password(mot_de_passe)
                utilisateur.save()
            utilisateurs[nom] = utilisateur

        categories = {}
        for cle, (nom, description) in CATEGORIES.items():
            categories[cle], _ = Categorie.objects.get_or_create(nom=nom, defaults={"description": description})

        evenements = {}
        for titre, type_evt, cle_cat, jours, heure, lieu, capacite, organisateur, description in EVENEMENTS:
            evenements[titre], _ = Evenement.objects.get_or_create(
                titre=titre,
                defaults={
                    "type_evenement": type_evt,
                    "categorie": categories[cle_cat],
                    "date": date_relative(jours, heure),
                    "lieu": lieu,
                    "capacite": capacite,
                    "organisateur": utilisateurs[organisateur],
                    "description": description,
                },
            )

        for nom, titre in INSCRIPTIONS:
            Inscription.objects.get_or_create(utilisateur=utilisateurs[nom], evenement=evenements[titre])

        self.stdout.write(self.style.SUCCESS("Données de démonstration chargées."))
        self.stdout.write("Comptes disponibles (développement uniquement) :")
        for nom, mot_de_passe, est_admin in UTILISATEURS:
            role = "administrateur" if est_admin else "utilisateur"
            self.stdout.write(f"  - {nom} / {mot_de_passe}  ({role})")
