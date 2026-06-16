from django.db import migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('analyse_hydrologique', '0002_stationhydrometrique_superficie_bv_jaugee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bassinversant',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PolygonField(
                blank=True, null=True, srid=4326, verbose_name='Géométrie'
            ),
        ),
        migrations.AlterField(
            model_name='stationpluviometrique',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PolygonField(
                blank=True, null=True, srid=4326, verbose_name='Géométrie (polygone)'
            ),
        ),
        migrations.AlterField(
            model_name='stationhydrometrique',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PointField(
                blank=True, null=True, srid=4326, verbose_name='Géométrie (point)'
            ),
        ),
    ]
