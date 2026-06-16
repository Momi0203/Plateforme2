import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0031_perimetre_volume_annee_humide_and_more'),
    ]

    operations = [
        # Périmètre : supprimer le champ geometrie (pas de géométrie sur un périmètre)
        migrations.RemoveField(
            model_name='perimetre',
            name='geometrie',
        ),

        # Ouvrages ponctuels : GeometryField → PointField
        migrations.AlterField(
            model_name='murprotection',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='barrageretenue',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='khettara',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='foragepuits',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='priselocale',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True),
        ),

        # Tronçon séguia : GeometryField → LineStringField
        migrations.AlterField(
            model_name='tronconseguia',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.LineStringField(
                blank=True, null=True, verbose_name='Géométrie'
            ),
        ),
    ]
