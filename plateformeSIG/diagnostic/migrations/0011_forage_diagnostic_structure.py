import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


SOURCE_ENERGIE_CHOICES = [
    ('electricite_reseau', 'Électricité réseau'),
    ('energie_solaire',    'Énergie solaire'),
    ('electrogene_diesel', 'Électrogène diesel'),
    ('systemes_hybrides',  'Systèmes hybrides'),
    ('electrique', 'Électrique (legacy)'),
    ('diesel',     'Diesel (legacy)'),
    ('solaire',    'Solaire (legacy)'),
    ('manuel',     'Manuel (legacy)'),
    ('autre',      'Autre (legacy)'),
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
        ('diagnostic', '0010_khettara_diagnostic_structure'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── ForagePuits : nom unique, géométrie polymorphe optionnelle, choix énergie enrichis
        migrations.AlterField(
            model_name='foragepuits',
            name='nom',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='foragepuits',
            name='source_energie_pompage',
            field=models.CharField(choices=SOURCE_ENERGIE_CHOICES, max_length=20),
        ),
        migrations.AlterField(
            model_name='foragepuits',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='foragepuits',
            name='etat_construction_fonctionnement',
            field=models.TextField(blank=True, help_text='Texte libre (legacy — voir EtatForagePuits)'),
        ),

        # ── Nouveau modèle EtatForagePuits
        migrations.CreateModel(
            name='EtatForagePuits',
            fields=[
                ('forage', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False,
                    related_name='diagnostic_etat',
                    to='diagnostic.foragepuits',
                )),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('etat_general', models.CharField(
                    blank=True, max_length=20,
                    choices=ETAT_GENERAL_CHOICES,
                    verbose_name='État général',
                )),
                ('valide', models.BooleanField(default=False, verbose_name='Validé')),
                ('qualite_physico_chimique_eau', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name="Qualité physico-chimique de l'eau")),
                ('degradation_structurelle_forage', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Dégradation structurelle du forage')),
                ('colmatage_forage', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Colmatage du forage')),
                ('etat_equipements', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='État des équipements')),
                ('editeur_operateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etat_forages_edites',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'État de forage/puits (diagnostic)',
                'verbose_name_plural': 'États des forages/puits (diagnostics)',
            },
        ),
    ]
