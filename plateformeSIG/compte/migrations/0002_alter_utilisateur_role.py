from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compte', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='utilisateur',
            name='role',
            field=models.CharField(
                choices=[
                    ('visiteur', 'Visiteur'),
                    ('operateur', 'Opérateur'),
                    ('editeur', 'Éditeur'),
                    ('administrateur', 'Administrateur'),
                ],
                default='visiteur',
                max_length=20,
            ),
        ),
    ]
