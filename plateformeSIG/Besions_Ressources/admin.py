from django.contrib import admin
from .models import (
    StationClimatique, Kc_Kr_culture, BilanBesoinRessources,
    BilanOuvrageAssocie,
)


@admin.register(StationClimatique)
class StationClimatiqueAdmin(admin.ModelAdmin):
    list_display = ['nom', 'latitude', 'x', 'y', 'created_at']
    search_fields = ['nom']


@admin.register(Kc_Kr_culture)
class Kc_Kr_cultureAdmin(admin.ModelAdmin):
    list_display = ['nom', 'updated_at']
    search_fields = ['nom']


class BilanOuvrageAssocieInline(admin.TabularInline):
    model = BilanOuvrageAssocie
    extra = 0
    fields = ('type_ouvrage', 'seuil', 'prise_locale', 'barrage', 'khettara',
              'forage', 'troncon_amenee', 'bassin_versant', 'tc_h',
              'tc_source', 'debit_troncon_m3s', 'ordre')
    readonly_fields = ('bassin_versant', 'tc_h', 'tc_source', 'debit_troncon_m3s')


@admin.register(BilanBesoinRessources)
class BilanBesoinRessourcesAdmin(admin.ModelAdmin):
    list_display = ['perimetre', 'station_climatique', 'station_hydrometrique',
                    'efficiance_reseau', 'est_calcule', 'date_calcul']
    list_filter = ['perimetre', 'station_hydrometrique']
    readonly_fields = ['resultats_eto', 'resultats_cultures', 'resultats_crue',
                       'resultats_bilan_normale', 'resultats_bilan_humide', 'date_calcul']
    inlines = [BilanOuvrageAssocieInline]

    @admin.display(boolean=True, description='Calculé')
    def est_calcule(self, obj):
        return obj.est_calcule


@admin.register(BilanOuvrageAssocie)
class BilanOuvrageAssocieAdmin(admin.ModelAdmin):
    list_display = ['bilan', 'type_ouvrage', 'troncon_amenee', 'tc_h', 'debit_troncon_m3s']
    list_filter = ['type_ouvrage']
