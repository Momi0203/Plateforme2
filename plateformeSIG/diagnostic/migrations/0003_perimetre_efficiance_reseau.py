from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0002_add_statut'),
    ]

    operations = [
        migrations.AddField(
            model_name='perimetre',
            name='efficiance_reseau',
            field=models.FloatField(
                default=0.9,
                help_text='Valeur entre 0 et 1 (défaut 0.9)',
                verbose_name="Efficiance du réseau d'irrigation",
            ),
        ),
    ]
