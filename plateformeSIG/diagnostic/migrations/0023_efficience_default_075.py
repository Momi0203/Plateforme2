# Module Bilan : defaut efficience reseau 0.75 sur tous les ouvrages

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0022_seguia_debit_m3s'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seuil',
            name='efficience_reseaux',
            field=models.FloatField(default=0.75, null=True, blank=True, help_text='Efficience du réseau (0–1, défaut 0.75)'),
        ),
        migrations.AlterField(
            model_name='priselocale',
            name='efficience_reseaux',
            field=models.FloatField(default=0.75, null=True, blank=True, help_text='Efficience du réseau (0–1, défaut 0.75)'),
        ),
        migrations.AlterField(
            model_name='khettara',
            name='efficience_reseaux',
            field=models.FloatField(default=0.75, null=True, blank=True, help_text='Efficience du réseau (0–1, défaut 0.75)'),
        ),
        migrations.AlterField(
            model_name='foragepuits',
            name='efficience_reseaux',
            field=models.FloatField(default=0.75, null=True, blank=True, help_text='Efficience du réseau (0–1, défaut 0.75)'),
        ),
        migrations.AlterField(
            model_name='barrageretenue',
            name='efficience_reseaux',
            field=models.FloatField(default=0.75, null=True, blank=True, help_text='Efficience du réseau (0–1, défaut 0.75)'),
        ),
        migrations.AlterField(
            model_name='murprotection',
            name='efficience_reseaux',
            field=models.FloatField(default=0.75, null=True, blank=True, help_text='Efficience du réseau (0–1, défaut 0.75)'),
        ),
        migrations.AlterField(
            model_name='seguias',
            name='efficience_trancons',
            field=models.FloatField(default=0.75, null=True, blank=True, help_text='Efficience des tronçons (0–1, défaut 0.75)'),
        ),
    ]
