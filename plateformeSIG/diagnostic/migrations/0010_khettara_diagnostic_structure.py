import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


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
        ('diagnostic', '0009_mur_diagnostic_structure'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Khettara : nom unique, géométrie optionnelle
        migrations.AlterField(
            model_name='khettara',
            name='nom',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='khettara',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='khettara',
            name='etat_construction_fonctionnement',
            field=models.TextField(blank=True, help_text='Texte libre (legacy — voir EtatKhettara)'),
        ),

        # ── Nouveau modèle EtatKhettara
        migrations.CreateModel(
            name='EtatKhettara',
            fields=[
                ('khettara', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False,
                    related_name='diagnostic_etat',
                    to='diagnostic.khettara',
                )),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('etat_general', models.CharField(
                    blank=True, max_length=20,
                    choices=ETAT_GENERAL_CHOICES,
                    verbose_name='État général',
                )),
                ('valide', models.BooleanField(default=False, verbose_name='Validé')),
                ('envasement_ensablement_fond', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Envasement / ensablement du fond')),
                ('degradation_beton', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Dégradation du béton')),
                ('accessibilite_entretien', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name="Accessibilité pour l'entretien")),
                ('stabilite_galerie_principale', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Stabilité de la galerie principale')),
                ('editeur_operateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etat_khettaras_edites',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'État de khettara (diagnostic)',
                'verbose_name_plural': 'États des khettaras (diagnostics)',
            },
        ),
    ]
