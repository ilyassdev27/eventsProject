import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Categorie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=100, unique=True, verbose_name="nom")),
                ("description", models.TextField(blank=True, verbose_name="description")),
            ],
            options={
                "verbose_name": "catégorie",
                "verbose_name_plural": "catégories",
                "ordering": ["nom"],
            },
        ),
        migrations.CreateModel(
            name="Evenement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titre", models.CharField(max_length=200, verbose_name="titre")),
                ("description", models.TextField(blank=True, verbose_name="description")),
                (
                    "type_evenement",
                    models.CharField(
                        choices=[
                            ("conference", "Conférence"),
                            ("atelier", "Atelier pratique"),
                            ("certification", "Certification"),
                        ],
                        default="conference",
                        max_length=20,
                        verbose_name="type d'événement",
                    ),
                ),
                ("date", models.DateTimeField(verbose_name="date et heure")),
                ("lieu", models.CharField(max_length=200, verbose_name="lieu")),
                (
                    "capacite",
                    models.PositiveIntegerField(
                        help_text="Nombre maximum de participants.",
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="capacité d'accueil",
                    ),
                ),
                ("date_creation", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                (
                    "categorie",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evenements",
                        to="events.categorie",
                        verbose_name="catégorie",
                    ),
                ),
                (
                    "organisateur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evenements_organises",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="organisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "événement",
                "verbose_name_plural": "événements",
                "ordering": ["date"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("capacite__gte", 1)),
                        name="evenement_capacite_au_moins_1",
                        violation_error_message="La capacité d'accueil doit être d'au moins 1 place.",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Inscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date_inscription", models.DateTimeField(auto_now_add=True, verbose_name="inscrit le")),
                (
                    "evenement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inscriptions",
                        to="events.evenement",
                        verbose_name="événement",
                    ),
                ),
                (
                    "utilisateur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inscriptions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "inscription",
                "verbose_name_plural": "inscriptions",
                "ordering": ["-date_inscription"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("utilisateur", "evenement"),
                        name="inscription_unique_par_utilisateur",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="evenement",
            name="participants",
            field=models.ManyToManyField(
                blank=True,
                related_name="evenements_suivis",
                through="events.Inscription",
                to=settings.AUTH_USER_MODEL,
                verbose_name="participants",
            ),
        ),
    ]
