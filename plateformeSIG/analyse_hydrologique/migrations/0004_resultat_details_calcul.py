from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyse_hydrologique', '0003_optional_geometry'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultatanalysehydrologique',
            name='details_calcul',
            field=models.JSONField(blank=True, null=True, verbose_name='Détails de calcul (JSON)'),
        ),
    ]
