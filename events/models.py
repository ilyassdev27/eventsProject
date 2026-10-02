"""
Modèles de l'application « events ».

- Categorie   : domaine technique (IA, DevOps, Cybersécurité...)
- Evenement   : conférence, atelier pratique ou certification
- Inscription : participation d'un utilisateur à un événement

Relations :
- Categorie 1 ──── N Evenement   (ForeignKey : One-to-Many)
- User      1 ──── N Evenement   (organisateur : One-to-Many)
- User      N ──── N Evenement   (participants : Many-to-Many via Inscription)
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Categorie(models.Model):
    """Domaine technique qui regroupe plusieurs événements."""

    nom = models.CharField("nom", max_length=100, unique=True)
    description = models.TextField("description", blank=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "catégorie"
        verbose_name_plural = "catégories"

    def __str__(self):
        return self.nom


class EvenementQuerySet(models.QuerySet):
    """Requêtes réutilisables sur les événements (appelées depuis les vues)."""

    def a_venir(self):
        return self.filter(date__gte=timezone.now())

    def termines(self):
        return self.filter(date__lt=timezone.now()).order_by("-date")

    def avec_nombre_inscrits(self):
        # Compte les inscriptions dans la même requête SQL
        # (évite une requête supplémentaire par événement affiché).
        return self.annotate(nb_inscrits=models.Count("inscriptions"))


class Evenement(models.Model):
    """Conférence, atelier pratique ou certification."""

    class TypeEvenement(models.TextChoices):
        CONFERENCE = "conference", "Conférence"
        ATELIER = "atelier", "Atelier pratique"
        CERTIFICATION = "certification", "Certification"

    titre = models.CharField("titre", max_length=200)
    description = models.TextField("description", blank=True)
    type_evenement = models.CharField(
        "type d'événement",
        max_length=20,
        choices=TypeEvenement.choices,
        default=TypeEvenement.CONFERENCE,
    )
    date = models.DateTimeField("date et heure")
    lieu = models.CharField("lieu", max_length=200)
    capacite = models.PositiveIntegerField(
        "capacité d'accueil",
        validators=[MinValueValidator(1)],
        help_text="Nombre maximum de participants.",
    )
    # One-to-Many : une catégorie contient plusieurs événements.
    # CASCADE : si une catégorie est supprimée, ses événements le sont aussi.
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.CASCADE,
        related_name="evenements",
        verbose_name="catégorie",
    )
    # L'utilisateur qui a créé l'événement : lui seul peut le modifier ou le supprimer.
    organisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="evenements_organises",
        verbose_name="organisateur",
    )
    # Many-to-Many : un utilisateur suit plusieurs événements et un événement
    # a plusieurs participants. La table intermédiaire est le modèle Inscription.
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Inscription",
        related_name="evenements_suivis",
        blank=True,
        verbose_name="participants",
    )
    date_creation = models.DateTimeField("créé le", auto_now_add=True)

    objects = EvenementQuerySet.as_manager()

    class Meta:
        ordering = ["date"]
        verbose_name = "événement"
        verbose_name_plural = "événements"
        constraints = [
            # Même règle que le validateur, mais garantie par la base de données.
            models.CheckConstraint(
                condition=models.Q(capacite__gte=1),
                name="evenement_capacite_au_moins_1",
                violation_error_message="La capacité d'accueil doit être d'au moins 1 place.",
            ),
        ]

    def __str__(self):
        return self.titre

    def get_absolute_url(self):
        return reverse("events:detail", args=[self.pk])

    # --- Statut calculé automatiquement (pas stocké en base) ----------------

    @property
    def est_termine(self):
        """Un événement est terminé dès que sa date est passée."""
        return self.date < timezone.now()

    @property
    def statut(self):
        return "Terminé" if self.est_termine else "À venir"

    # --- Places -------------------------------------------------------------

    @property
    def nombre_inscrits(self):
        # Valeur déjà calculée si la vue a utilisé avec_nombre_inscrits().
        if hasattr(self, "nb_inscrits"):
            return self.nb_inscrits
        return self.inscriptions.count()

    @property
    def places_restantes(self):
        return max(self.capacite - self.nombre_inscrits, 0)

    @property
    def est_complet(self):
        return self.places_restantes == 0

    # --- Permissions --------------------------------------------------------

    def peut_etre_modifie_par(self, utilisateur):
        """Seul l'organisateur (ou un superutilisateur) peut modifier ou supprimer."""
        return utilisateur.is_authenticated and (
            utilisateur.pk == self.organisateur_id or utilisateur.is_superuser
        )


class Inscription(models.Model):
    """Participation d'un utilisateur à un événement (table intermédiaire)."""

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inscriptions",
        verbose_name="utilisateur",
    )
    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name="inscriptions",
        verbose_name="événement",
    )
    date_inscription = models.DateTimeField("inscrit le", auto_now_add=True)

    class Meta:
        ordering = ["-date_inscription"]
        verbose_name = "inscription"
        verbose_name_plural = "inscriptions"
        constraints = [
            # Un utilisateur ne peut s'inscrire qu'une seule fois au même événement.
            models.UniqueConstraint(
                fields=["utilisateur", "evenement"],
                name="inscription_unique_par_utilisateur",
            ),
        ]

    def __str__(self):
        return f"{self.utilisateur} → {self.evenement}"
