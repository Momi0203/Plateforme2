import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


RIVE_CHOICES = [
    ('droite', 'Rive droite'),
    ('gauche', 'Rive gauche'),
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
        ('diagnostic', '0008_seguia_diagnostic_structure'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── MurProtection : nom unique optionnel, libellés rive enrichis, géométrie optionnelle
        migrations.AddField(
            model_name='murprotection',
            name='nom_mur_protection',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='murprotection',
            name='rive',
            field=models.CharField(choices=RIVE_CHOICES, max_length=20),
        ),
        migrations.AlterField(
            model_name='murprotection',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='murprotection',
            name='etat_construction',
            field=models.TextField(blank=True, help_text='Texte libre (legacy — voir EtatMurProtection)'),
        ),

        # ── Nouveau modèle EtatMurProtection
        migrations.CreateModel(
            name='EtatMurProtection',
            fields=[
                ('mur', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False,
                    related_name='diagnostic_etat',
                    to='diagnostic.murprotection',
                )),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('etat_general', models.CharField(
                    blank=True, max_length=20,
                    choices=ETAT_GENERAL_CHOICES,
                    verbose_name='État général',
                )),
                ('valide', models.BooleanField(default=False, verbose_name='Validé')),
                ('fissures_revetement', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Fissures du revêtement')),
                ('degradation_beton', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Dégradation du béton')),
                ('risque_contournement', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Risque de contournement')),
                ('editeur_operateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etat_murs_edites',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'État de mur (diagnostic)',
                'verbose_name_plural': 'États des murs (diagnostics)',
            },
        ),
    ]
