import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


FORME_PERTUIS_CHOICES = [
    ('trapezoidale', 'Trapézoïdale'),
    ('rectangulaire', 'Rectangulaire'),
    ('circulaire', 'Circulaire'),
]

ETAT_GENERAL_CHOICES = [
    ('t_mauvais',     'Très mauvais'),
    ('mauvais',       'Mauvais'),
    ('moyen_mauvais', 'Moyen-mauvais'),
    ('moyen',         'Moyen'),
    ('moyen_bon',     'Moyen-bon'),
    ('bon',           'Bon'),
    ('excellent',     'Excellent'),
]

NOTE_SEGUIA_CHOICES = [
    (0, 'Absence de désordre / état normal'),
    (1, 'Très bon état'),
    (2, 'Dégradation légère'),
    (3, 'Dégradation modérée'),
    (4, 'Dégradation importante'),
    (5, 'État critique / risque élevé'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0012_barrage_diagnostic_structure'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── PriseLocale : nom unique, forme optionnelle, ajout coords / matériaux / débit / géométrie
        migrations.AlterField(
            model_name='priselocale',
            name='nom',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='priselocale',
            name='forme_pertuis',
            field=models.CharField(blank=True, choices=FORME_PERTUIS_CHOICES, max_length=20),
        ),
        migrations.AddField(
            model_name='priselocale',
            name='coordonnee_x',
            field=models.FloatField(blank=True, help_text='Nord Maroc X (m)', null=True),
        ),
        migrations.AddField(
            model_name='priselocale',
            name='coordonnee_y',
            field=models.FloatField(blank=True, help_text='Nord Maroc Y (m)', null=True),
        ),
        migrations.AddField(
            model_name='priselocale',
            name='materiaux_construction',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='priselocale',
            name='debit_derive',
            field=models.FloatField(blank=True, help_text='m³/s', null=True),
        ),
        migrations.AddField(
            model_name='priselocale',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='priselocale',
            name='etat_fonctionnement',
            field=models.TextField(blank=True, help_text='Texte libre (legacy — voir EtatPriseLocale)'),
        ),

        # ── Nouveau modèle EtatPriseLocale
        migrations.CreateModel(
            name='EtatPriseLocale',
            fields=[
                ('prise', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False,
                    related_name='diagnostic_etat',
                    to='diagnostic.priselocale',
                )),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('etat_general', models.CharField(
                    blank=True, max_length=20,
                    choices=ETAT_GENERAL_CHOICES,
                    verbose_name='État général',
                )),
                ('valide', models.BooleanField(default=False, verbose_name='Validé')),
                ('envasement_sedimentation_entree', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name="Envasement / sédimentation à l'entrée")),
                ('degradation_revetement', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Dégradation du revêtement')),
                ('accumulation_debris_vegetation', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Accumulation de débris / végétation')),
                ('etat_dispositifs_regulation', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='État des dispositifs de régulation (vannes, masques)')),
                ('protection_crues_debordements', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Protection contre crues / débordements')),
                ('editeur_operateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etat_prises_edites',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'État de prise locale (diagnostic)',
                'verbose_name_plural': 'États des prises locales (diagnostics)',
            },
        ),
    ]
