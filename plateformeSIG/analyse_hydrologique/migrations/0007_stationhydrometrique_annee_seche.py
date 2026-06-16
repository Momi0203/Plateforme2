# Generated for module Bilan Besoin-Ressources : ajout des donnees annee seche

import django.contrib.postgres.fields
from django.db import migrations, models

_JOURS_PAR_MOIS = [30, 31, 30, 31, 31, 28, 31, 30, 31, 30, 31, 31]


def _init_seche_defaults(apps, schema_editor):
    StationHydrometrique = apps.get_model('analyse_hydrologique', 'StationHydrometrique')
    for station in StationHydrometrique.objects.all():
        updated = False
        if not station.frequences_mensuelles_annee_seche:
            station.frequences_mensuelles_annee_seche = list(_JOURS_PAR_MOIS)
            updated = True
        if updated:
            station.save(update_fields=['frequences_mensuelles_annee_seche'])


class Migration(migrations.Migration):

    dependencies = [
        ('analyse_hydrologique', '0006_stationhydrometrique_debits_mensuels_annee_normale_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stationhydrometrique',
            name='debits_mensuels_annee_seche',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), blank=True, default=list, size=12, verbose_name='Débits mensuels année sèche (m³/s, Sep→Aoû)'),
        ),
        migrations.AddField(
            model_name='stationhydrometrique',
            name='frequences_mensuelles_annee_seche',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, default=list, size=12, verbose_name='Fréquences mensuelles année sèche (jours, Sep→Aoû)'),
        ),
        migrations.RunPython(_init_seche_defaults, migrations.RunPython.noop),
    ]
