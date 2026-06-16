import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


TRONCON_CHOICES = [(f'TR{i}', f'TR{i}') for i in range(1, 21)]

NATURE_SEGUIA_CHOICES = [
    ('beton',      'Béton'),
    ('beton_arme', 'Béton armé'),
    ('terre',      'Terre'),
    ('autre',      'Autre'),
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
        ('diagnostic', '0007_seuil_diagnostic_structure'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Seguias : nom unique, choix tronçon, choix nature étendu, géom optionnelle
        migrations.AlterField(
            model_name='seguias',
            name='nom_de_la_seguia',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='seguias',
            name='troncon',
            field=models.CharField(blank=True, choices=TRONCON_CHOICES, max_length=10),
        ),
        migrations.AlterField(
            model_name='seguias',
            name='nature',
            field=models.CharField(choices=NATURE_SEGUIA_CHOICES, max_length=20),
        ),
        migrations.AlterField(
            model_name='seguias',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='seguias',
            name='etat',
            field=models.TextField(blank=True, help_text='Texte libre (legacy — voir EtatSeguia)'),
        ),

        # ── Nouveau modèle EtatSeguia
        migrations.CreateModel(
            name='EtatSeguia',
            fields=[
                ('seguia', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False,
                    related_name='diagnostic_etat',
                    to='diagnostic.seguias',
                )),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('etat_general', models.CharField(
                    blank=True, max_length=20,
                    choices=ETAT_GENERAL_CHOICES,
                    verbose_name='État général',
                )),
                ('valide', models.BooleanField(default=False, verbose_name='Validé')),
                ('fissures_revetement', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Fissures du revêtement')),
                ('infiltration_fuite', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Infiltration / fuite')),
                ('obstructions_debris', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Obstructions / débris')),
                ('erosion_berges', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Érosion des berges')),
                ('sedimentation_fond', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Sédimentation au fond')),
                ('ouvrages_regulation', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Ouvrages de régulation')),
                ('spalling_beton', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Spalling du béton')),
                ('editeur_operateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etat_seguias_edites',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'État de séguia (diagnostic)',
                'verbose_name_plural': 'États des séguias (diagnostics)',
            },
        ),
    ]
