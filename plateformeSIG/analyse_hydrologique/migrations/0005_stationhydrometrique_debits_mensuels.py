from django.db import migrations, models
from django.contrib.postgres.fields import ArrayField


class Migration(migrations.Migration):

    dependencies = [
        ('analyse_hydrologique', '0004_resultat_details_calcul'),
    ]

    operations = [
        migrations.AddField(
            model_name='stationhydrometrique',
            name='debits_mensuels_annee_humide',
            field=ArrayField(
                base_field=models.FloatField(),
                blank=True,
                default=list,
                size=12,
                verbose_name='Débits mensuels année humide (m³/s, Sep→Aoû)',
            ),
        ),
    ]
