from django.contrib import admin

from .models import Efficience


@admin.register(Efficience)
class EfficienceAdmin(admin.ModelAdmin):
    list_display = (
        'perimetre',
        'ouvrage_tete_type',
        'ouvrage_tete_id',
        'efficience_globale',
        'efficience_principale',
        'efficience_secondaire',
        'efficience_tertiaire',
        'date_calcul',
        'operateur',
    )
    list_filter = ('ouvrage_tete_type', 'date_calcul', 'perimetre')
    search_fields = ('perimetre__ksar_village', 'perimetre__commune_territoriale')
    readonly_fields = ('date_calcul',)
    ordering = ('-date_calcul',)
