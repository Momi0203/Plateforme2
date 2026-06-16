from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import BassinVersant, ReseauHydrographique, Province, Commune


@admin.register(BassinVersant)
class BassinVersantAdmin(GISModelAdmin):
    list_display = ("nom", "superficie_km2", "perimetre_km", "altitude_min", "altitude_max", "thalweg_km")
    search_fields = ("nom",)
    ordering = ("nom",)


@admin.register(ReseauHydrographique)
class ReseauHydrographiqueAdmin(GISModelAdmin):
    list_display = ("pk", "bassin_versant", "comid", "sorder")
    list_filter = ("bassin_versant", "sorder")
    raw_id_fields = ("bassin_versant",)


@admin.register(Province)
class ProvinceAdmin(GISModelAdmin):
    list_display = ("nom_fr", "superficie_km2", "population_totale")
    search_fields = ("nom_fr",)


@admin.register(Commune)
class CommuneAdmin(GISModelAdmin):
    list_display = ("nom_fr", "province", "type_commune", "population_totale")
    list_filter = ("province", "type_commune")
    search_fields = ("nom_fr",)
