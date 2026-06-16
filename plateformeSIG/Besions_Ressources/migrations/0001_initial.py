import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('diagnostic', '0003_perimetre_efficiance_reseau'),
        ('analyse_hydrologique', '0004_resultat_details_calcul'),
    ]

    operations = [
        migrations.CreateModel(
            name='StationClimatique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name='Nom de la station')),
                ('latitude', models.FloatField(verbose_name='Latitude (degrés)')),
                ('temperatures_moyennes', models.JSONField(help_text='12 valeurs Sep→Aoû', verbose_name='Températures moyennes (°C)')),
                ('taux_insolation', models.JSONField(help_text='12 valeurs Sep→Aoû (0–1)', verbose_name="Taux d'insolation n/N")),
                ('precipitations_normales', models.JSONField(help_text='12 valeurs Sep→Aoû', verbose_name='Précipitations année normale (mm/mois)')),
                ('precipitations_humides', models.JSONField(blank=True, help_text='12 valeurs Sep→Aoû', null=True, verbose_name='Précipitations année humide (mm/mois)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('perimetre', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stations_climatiques', to='diagnostic.perimetre', verbose_name='Périmètre associé')),
            ],
            options={
                'verbose_name': 'Station Climatique',
                'verbose_name_plural': 'Stations Climatiques',
            },
        ),
        migrations.CreateModel(
            name='CulturePerimetre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name='Culture')),
                ('kc', models.JSONField(help_text='12 valeurs Sep→Aoû', verbose_name='Kc mensuel')),
                ('kr', models.JSONField(help_text='12 valeurs Sep→Aoû', verbose_name='Kr mensuel')),
                ('superficie_ha', models.FloatField(verbose_name='Superficie (ha)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('perimetre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cultures_bilan', to='diagnostic.perimetre', verbose_name='Périmètre')),
            ],
            options={
                'verbose_name': 'Culture du périmètre',
                'verbose_name_plural': 'Cultures du périmètre',
            },
        ),
        migrations.CreateModel(
            name='BilanBesoinRessources',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('efficiance_reseau', models.FloatField(default=0.9, verbose_name='Efficiance du réseau (0–1)')),
                ('debits_mensuels_m3s', models.JSONField(blank=True, help_text='12 valeurs Sep→Aoû', null=True, verbose_name='Débits mensuels station (m³/s)')),
                ('superficie_bv_jaugee_km2', models.FloatField(blank=True, null=True, verbose_name='Superficie BV jaugé (km²)')),
                ('tc_h', models.FloatField(blank=True, null=True, verbose_name='Temps de concentration (h)')),
                ('canal_b', models.FloatField(blank=True, null=True, verbose_name='Largeur fond canal b (m)')),
                ('canal_y', models.FloatField(blank=True, null=True, verbose_name='Hauteur eau canal y (m)')),
                ('canal_z', models.FloatField(blank=True, null=True, verbose_name='Fruit de berge z')),
                ('canal_pente', models.FloatField(blank=True, null=True, verbose_name='Pente canal (m/m)')),
                ('canal_manning_n', models.FloatField(default=0.015, verbose_name='Coefficient Manning n')),
                ('coeff_humide', models.FloatField(default=1.3, verbose_name='Coefficient année humide')),
                ('autres_ressources', models.JSONField(blank=True, null=True, verbose_name='Autres ressources')),
                ('resultats_eto', models.JSONField(blank=True, null=True)),
                ('resultats_cultures', models.JSONField(blank=True, null=True)),
                ('resultats_crue', models.JSONField(blank=True, null=True)),
                ('resultats_bilan_normale', models.JSONField(blank=True, null=True)),
                ('resultats_bilan_humide', models.JSONField(blank=True, null=True)),
                ('date_calcul', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('perimetre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bilans_ressources', to='diagnostic.perimetre', verbose_name='Périmètre')),
                ('station_climatique', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Besions_Ressources.stationclimatique', verbose_name='Station climatique')),
                ('bassin_versant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='analyse_hydrologique.bassinversant', verbose_name='Bassin versant')),
            ],
            options={
                'verbose_name': 'Bilan Besoin-Ressources',
                'verbose_name_plural': 'Bilans Besoin-Ressources',
                'ordering': ['-created_at'],
            },
        ),
    ]
