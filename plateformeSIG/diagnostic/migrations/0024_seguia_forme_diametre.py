from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0023_efficience_default_075'),
    ]

    operations = [
        migrations.AddField(
            model_name='seguias',
            name='forme',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('trapezoidale', 'Trapézoïdale'),
                    ('rectangulaire', 'Rectangulaire'),
                    ('circulaire', 'Circulaire'),
                ],
                default='trapezoidale',
                verbose_name='Forme',
            ),
        ),
        migrations.AddField(
            model_name='seguias',
            name='diametre',
            field=models.FloatField(
                null=True, blank=True,
                verbose_name='Diamètre',
                help_text='Diamètre (m) — requis pour la forme circulaire',
            ),
        ),
        migrations.AlterField(
            model_name='seguias',
            name='largeur_meroire',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='seguias',
            name='hauteur',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='seguias',
            name='fruit_de_berge',
            field=models.FloatField(null=True, blank=True, default=0),
        ),
    ]
