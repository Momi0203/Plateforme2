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
        ('diagnostic', '0011_forage_diagnostic_structure'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── BarrageRetenue : nom unique, géométrie polymorphe optionnelle
        migrations.AlterField(
            model_name='barrageretenue',
            name='nom',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='barrageretenue',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='barrageretenue',
            name='etat_construction_fonctionnement',
            field=models.TextField(blank=True, help_text='Texte libre (legacy — voir EtatBarrageRetenue)'),
        ),

        # ── Nouveau modèle EtatBarrageRetenue
        migrations.CreateModel(
            name='EtatBarrageRetenue',
            fields=[
                ('barrage', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False,
                    related_name='diagnostic_etat',
                    to='diagnostic.barrageretenue',
                )),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('etat_general', models.CharField(
                    blank=True, max_length=20,
                    choices=ETAT_GENERAL_CHOICES,
                    verbose_name='État général',
                )),
                ('valide', models.BooleanField(default=False, verbose_name='Validé')),
                ('affouillement_pied_digue_aval', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Affouillement au pied de digue aval')),
                ('taux_envasement_retenue', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name="Taux d'envasement de la retenue")),
                ('regulation_debits_aval', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name='Régulation des débits aval')),
                ('fonctionnement_ouvrages_prise_eau', models.IntegerField(blank=True, choices=NOTE_SEGUIA_CHOICES, null=True, verbose_name="Fonctionnement des ouvrages de prise d'eau")),
                ('editeur_operateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etat_barrages_edites',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'État de barrage (diagnostic)',
                'verbose_name_plural': 'États des barrages (diagnostics)',
            },
        ),
    ]
