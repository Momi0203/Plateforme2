import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0004_barrageretenue_date_diagnostic_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PriseLocale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('defaut_ouvrage', models.TextField(blank=True, default='', help_text='Texte libre sur les défauts observés')),
                ('nom', models.CharField(max_length=100)),
                ('forme_pertuis', models.CharField(
                    choices=[
                        ('trapezoidale', 'Trapézoïdale'),
                        ('rectangulaire', 'Rectangulaire'),
                        ('circulaire', 'Circulaire'),
                    ],
                    max_length=20,
                )),
                ('largeur_au_miroir', models.FloatField(blank=True, help_text='m', null=True)),
                ('hauteur_pertuis', models.FloatField(blank=True, help_text='m', null=True)),
                ('fruit_pente', models.FloatField(blank=True, help_text='m (fruit de la pente)', null=True)),
                ('diametre', models.FloatField(blank=True, help_text='m', null=True)),
                ('etat_fonctionnement', models.TextField(blank=True, help_text='Texte libre')),
                ('statut', models.CharField(
                    choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                    default='brouillon',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('perimetre', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='prises_locales',
                    to='diagnostic.perimetre',
                )),
                ('saisi_par', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='diagnostic_priselocale_saisis',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('valide_par', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='diagnostic_priselocale_valides',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name_plural': 'Prises locales',
            },
        ),
    ]
