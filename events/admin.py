"""Configuration de l'interface d'administration (/admin/)."""

from django.contrib import admin
from django.db.models import Count

from .models import Categorie, Evenement, Inscription

admin.site.site_header = "TechEvents · Administration"
admin.site.site_title = "TechEvents"


class InscriptionInline(admin.TabularInline):
    """Affiche les inscrits directement dans la fiche d'un événement."""

    model = Inscription
    extra = 0


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ["nom", "nombre_evenements"]
    search_fields = ["nom"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(nb_evenements=Count("evenements"))

    @admin.display(description="événements", ordering="nb_evenements")
    def nombre_evenements(self, categorie):
        return categorie.nb_evenements


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ["titre", "categorie", "type_evenement", "date", "lieu", "capacite", "organisateur"]
    list_filter = ["categorie", "type_evenement"]
    search_fields = ["titre", "lieu", "description"]
    date_hierarchy = "date"
    inlines = [InscriptionInline]


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "evenement", "date_inscription"]
    list_filter = ["evenement__categorie"]
    search_fields = ["utilisateur__username", "evenement__titre"]
