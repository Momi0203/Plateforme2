import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carte', '0001_initial'),
        ('diagnostic', '0025_perimetre_et0_mm_jour_seguias_date_dernier_calcul_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perimetre',
            name='commune',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='perimetres',
                to='carte.commune',
                to_field='nom_fr',
                verbose_name='Commune (entité)',
            ),
        ),
    ]
