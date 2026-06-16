from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='perimetre',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='seuil',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='murprotection',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='seguias',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='barrageretenue',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='khettara',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='foragepuits',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
            ),
        ),
    ]
