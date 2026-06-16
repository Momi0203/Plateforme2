import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Province',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_fr', models.CharField(max_length=100)),
                ('nom_ar', models.CharField(max_length=100)),
                ('annee_refe', models.IntegerField()),
                ('population_totale', models.IntegerField()),
                ('population_urbaine', models.IntegerField()),
                ('nombre_menages', models.IntegerField()),
                ('superficie_km2', models.DecimalField(decimal_places=2, max_digits=12)),
                ('densite_hab_km2', models.DecimalField(decimal_places=2, max_digits=10)),
                ('taux_urbanisation_pct', models.DecimalField(decimal_places=2, max_digits=5)),
                ('taux_accroissement_pct', models.DecimalField(decimal_places=2, max_digits=5)),
                ('communes_urbaines', models.IntegerField()),
                ('communes_rurales', models.IntegerField()),
                ('station_meteo', models.CharField(max_length=50)),
                ('temp_moy_annuelle_c', models.DecimalField(decimal_places=1, max_digits=4)),
                ('precip_annuelle_mm', models.DecimalField(decimal_places=1, max_digits=8)),
                ('humidite_rel_moy_pct', models.DecimalField(decimal_places=1, max_digits=4)),
                ('et0_moy_journaliere_mm_j', models.DecimalField(decimal_places=2, max_digits=5)),
                ('et0_annuelle_mm', models.DecimalField(decimal_places=1, max_digits=8)),
                ('geometrie', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name_plural': 'Provinces'},
        ),
        migrations.CreateModel(
            name='Commune',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_fr', models.CharField(max_length=100, unique=True)),
                ('nom_ar', models.CharField(max_length=100)),
                ('annee_refe', models.IntegerField(blank=True, null=True)),
                ('type_commune', models.CharField(choices=[('Urbaine', 'Urbaine'), ('Rurale', 'Rurale')], max_length=10)),
                ('population_totale', models.IntegerField()),
                ('nombre_menages', models.IntegerField()),
                ('superficie_km2', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('station_meteo', models.CharField(max_length=50)),
                ('temp_moy_annuelle_c', models.DecimalField(decimal_places=1, max_digits=4)),
                ('precip_annuelle_mm', models.DecimalField(decimal_places=1, max_digits=8)),
                ('humidite_rel_moy_pct', models.DecimalField(decimal_places=1, max_digits=4)),
                ('et0_moy_journaliere_mm_j', models.DecimalField(decimal_places=2, max_digits=5)),
                ('et0_annuelle_mm', models.DecimalField(decimal_places=1, max_digits=8)),
                ('nbr_perimetres_agricoles', models.IntegerField(blank=True, null=True)),
                ('geometrie', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('province', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='communes', to='carte.province')),
            ],
            options={'verbose_name_plural': 'Communes'},
        ),
    ]
