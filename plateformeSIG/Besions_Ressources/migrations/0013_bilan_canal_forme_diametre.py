# Ajout des champs canal_forme et canal_diametre sur BilanBesoinRessources
# pour supporter les tronçons à section circulaire (en plus de trapézoïdale et
# rectangulaire).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0012_seuil_deuxieme_troncon'),
    ]

    operations = [
        migrations.AddField(
            model_name='bilanbesoinressources',
            name='canal_forme',
            field=models.CharField(
                choices=[
                    ('trapezoidale',  'Trapézoïdale'),
                    ('rectangulaire', 'Rectangulaire'),
                    ('circulaire',    'Circulaire'),
                ],
                default='trapezoidale',
                max_length=20,
                verbose_name='Forme de section',
            ),
        ),
        migrations.AddField(
            model_name='bilanbesoinressources',
            name='canal_diametre',
            field=models.FloatField(
                blank=True, null=True,
                verbose_name='Diamètre canal (m)',
                help_text='Requis si forme circulaire',
            ),
        ),
    ]
