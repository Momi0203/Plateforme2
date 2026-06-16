from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('efficiences', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='efficience',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
                verbose_name='Statut',
            ),
        ),
    ]
