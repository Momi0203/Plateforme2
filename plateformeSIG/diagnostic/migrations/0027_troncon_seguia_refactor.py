"""
Migration 0027 : Refactorisation Séguia → table parente + TronconSeguia + EtatTronconSeguia.
"""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.contrib.gis.db.models.fields


def _migrate_seguias_to_troncons(apps, schema_editor):
    """Chaque ligne Seguias existante devient un TronconSeguia (troncon = TR1 si vide)."""
    Seguias = apps.get_model('diagnostic', 'Seguias')
    TronconSeguia = apps.get_model('diagnostic', 'TronconSeguia')
    for seg in Seguias.objects.all():
        troncon = getattr(seg, 'troncon', '') or 'TR1'
        TronconSeguia.objects.create(
            seguia=seg,
            troncon=troncon,
            forme=getattr(seg, 'forme', 'trapezoidale') or 'trapezoidale',
            longueur=getattr(seg, 'longueur', 0) or 0,
            largeur_meroire=getattr(seg, 'largeur_meroire', None),
            hauteur=getattr(seg, 'hauteur', None),
            hauteur_eau=getattr(seg, 'hauteur_eau', 0) or 0,
            fruit_de_berge=getattr(seg, 'fruit_de_berge', 0),
            epaisseur_parois=getattr(seg, 'epaisseur_parois', 0) or 0,
            diametre=getattr(seg, 'diametre', None),
            nature=getattr(seg, 'nature', 'beton') or 'beton',
            debit=getattr(seg, 'debit', 0) or 0,
            type_decoulement=getattr(seg, 'type_decoulement', 'ciel_ouvert') or 'ciel_ouvert',
            efficience_trancons=getattr(seg, 'efficience_trancons', 0.75),
            efficience_calculee=getattr(seg, 'efficience_calculee', None),
            perte_infiltration_m3s=getattr(seg, 'perte_infiltration_m3s', None),
            perte_vaporisation_m3s=getattr(seg, 'perte_vaporisation_m3s', None),
            date_dernier_calcul=getattr(seg, 'date_dernier_calcul', None),
            geometrie=getattr(seg, 'geometrie', None),
        )


def _migrate_etat_seguia_to_troncon(apps, schema_editor):
    """Migre chaque EtatSeguia vers EtatTronconSeguia via le TronconSeguia créé."""
    EtatSeguia = apps.get_model('diagnostic', 'EtatSeguia')
    TronconSeguia = apps.get_model('diagnostic', 'TronconSeguia')
    EtatTronconSeguia = apps.get_model('diagnostic', 'EtatTronconSeguia')
    for etat in EtatSeguia.objects.all():
        try:
            troncon = TronconSeguia.objects.get(seguia_id=etat.seguia_id)
        except TronconSeguia.DoesNotExist:
            continue
        EtatTronconSeguia.objects.create(
            troncon=troncon,
            date_diagnostic=etat.date_diagnostic,
            etat_general=etat.etat_general,
            valide=etat.valide,
            fissures_revetement=etat.fissures_revetement,
            infiltration_fuite=etat.infiltration_fuite,
            obstructions_debris=etat.obstructions_debris,
            erosion_berges=etat.erosion_berges,
            sedimentation_fond=etat.sedimentation_fond,
            ouvrages_regulation=etat.ouvrages_regulation,
            spalling_beton=etat.spalling_beton,
            editeur_operateur=etat.editeur_operateur,
        )


NOTE_SEGUIA = [
    (0, 'Absence de désordre / état normal'), (1, 'Très bon état'),
    (2, 'Dégradation légère'), (3, 'Dégradation modérée'),
    (4, 'Dégradation importante'), (5, 'État critique / risque élevé'),
]
ETAT_DIAG = [
    ('t_mauvais', 'Très mauvais'), ('mauvais', 'Mauvais'),
    ('moyen_mauvais', 'Moyen-mauvais'), ('moyen', 'Moyen'),
    ('moyen_bon', 'Moyen-bon'), ('bon', 'Bon'), ('excellent', 'Excellent'),
]
TRONCON_CH = [(f'TR{i}', f'TR{i}') for i in range(1, 21)]


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0026_perimetre_commune_to_field_nomfr'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. Créer TronconSeguia ────────────────────────────────────────────
        migrations.CreateModel(
            name='TronconSeguia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('troncon', models.CharField(choices=TRONCON_CH, max_length=10, verbose_name='Tronçon')),
                ('forme', models.CharField(
                    choices=[('trapezoidale', 'Trapézoïdale'), ('rectangulaire', 'Rectangulaire'), ('circulaire', 'Circulaire')],
                    default='trapezoidale', max_length=20, verbose_name='Forme')),
                ('longueur', models.FloatField(verbose_name='Longueur (m)')),
                ('largeur_meroire', models.FloatField(blank=True, null=True, verbose_name='Largeur miroir (m)')),
                ('hauteur', models.FloatField(blank=True, null=True, verbose_name='Hauteur (m)')),
                ('hauteur_eau', models.FloatField(verbose_name="Hauteur d'eau (m)")),
                ('fruit_de_berge', models.FloatField(blank=True, default=0, null=True, verbose_name='Fruit de berge')),
                ('epaisseur_parois', models.FloatField(verbose_name='Épaisseur parois (m)')),
                ('diametre', models.FloatField(blank=True, null=True, verbose_name='Diamètre (m)')),
                ('nature', models.CharField(
                    choices=[('beton', 'Béton'), ('beton_arme', 'Béton armé'), ('terre', 'Terre'), ('autre', 'Autre')],
                    max_length=20, verbose_name='Nature')),
                ('debit', models.FloatField(verbose_name='Débit (m³/s)')),
                ('type_decoulement', models.CharField(
                    choices=[('dalot', 'Dalot'), ('ciel_ouvert', 'À ciel ouvert')],
                    max_length=20, verbose_name="Type d'écoulement")),
                ('efficience_trancons', models.FloatField(blank=True, default=0.75, null=True, verbose_name='Efficience saisie (0–1)')),
                ('efficience_calculee', models.FloatField(blank=True, null=True, verbose_name='Efficience calculée (%)')),
                ('perte_infiltration_m3s', models.FloatField(blank=True, null=True, verbose_name='Perte infiltration (m³/s)')),
                ('perte_vaporisation_m3s', models.FloatField(blank=True, null=True, verbose_name='Perte évaporation (m³/s)')),
                ('date_dernier_calcul', models.DateTimeField(blank=True, null=True, verbose_name='Date dernier calcul')),
                ('geometrie', django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326, verbose_name='Géométrie')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('seguia', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='troncons',
                    to='diagnostic.seguias',
                    verbose_name='Séguia parente')),
            ],
            options={
                'verbose_name': 'Tronçon de séguia',
                'verbose_name_plural': 'Tronçons de séguias',
                'ordering': ['seguia', 'troncon'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='tronconseguia',
            unique_together={('seguia', 'troncon')},
        ),

        # ── 2. Migrer Seguias → TronconSeguia ────────────────────────────────
        migrations.RunPython(_migrate_seguias_to_troncons, migrations.RunPython.noop),

        # ── 3. Créer EtatTronconSeguia ────────────────────────────────────────
        migrations.CreateModel(
            name='EtatTronconSeguia',
            fields=[
                ('troncon', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False,
                    related_name='diagnostic_etat',
                    to='diagnostic.tronconseguia')),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('etat_general', models.CharField(blank=True, choices=ETAT_DIAG, max_length=20, verbose_name='État général')),
                ('valide', models.BooleanField(default=False, verbose_name='Validé')),
                ('fissures_revetement', models.IntegerField(blank=True, choices=NOTE_SEGUIA, null=True, verbose_name='Fissures du revêtement')),
                ('infiltration_fuite', models.IntegerField(blank=True, choices=NOTE_SEGUIA, null=True, verbose_name='Infiltration / fuite')),
                ('obstructions_debris', models.IntegerField(blank=True, choices=NOTE_SEGUIA, null=True, verbose_name='Obstructions / débris')),
                ('erosion_berges', models.IntegerField(blank=True, choices=NOTE_SEGUIA, null=True, verbose_name='Érosion des berges')),
                ('sedimentation_fond', models.IntegerField(blank=True, choices=NOTE_SEGUIA, null=True, verbose_name='Sédimentation au fond')),
                ('ouvrages_regulation', models.IntegerField(blank=True, choices=NOTE_SEGUIA, null=True, verbose_name='Ouvrages de régulation')),
                ('spalling_beton', models.IntegerField(blank=True, choices=NOTE_SEGUIA, null=True, verbose_name='Spalling du béton')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('editeur_operateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etat_troncons_seguia_edites',
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'État de tronçon de séguia (diagnostic)',
                'verbose_name_plural': 'États des tronçons de séguias (diagnostics)',
            },
        ),

        # ── 4. Migrer EtatSeguia → EtatTronconSeguia ─────────────────────────
        migrations.RunPython(_migrate_etat_seguia_to_troncon, migrations.RunPython.noop),

        # ── 5. Supprimer les champs de dimension/efficience/géométrie de Seguias
        migrations.RemoveField(model_name='seguias', name='troncon'),
        migrations.RemoveField(model_name='seguias', name='forme'),
        migrations.RemoveField(model_name='seguias', name='longueur'),
        migrations.RemoveField(model_name='seguias', name='largeur_meroire'),
        migrations.RemoveField(model_name='seguias', name='hauteur'),
        migrations.RemoveField(model_name='seguias', name='hauteur_eau'),
        migrations.RemoveField(model_name='seguias', name='fruit_de_berge'),
        migrations.RemoveField(model_name='seguias', name='epaisseur_parois'),
        migrations.RemoveField(model_name='seguias', name='diametre'),
        migrations.RemoveField(model_name='seguias', name='nature'),
        migrations.RemoveField(model_name='seguias', name='debit'),
        migrations.RemoveField(model_name='seguias', name='type_decoulement'),
        migrations.RemoveField(model_name='seguias', name='etat'),
        migrations.RemoveField(model_name='seguias', name='efficience_trancons'),
        migrations.RemoveField(model_name='seguias', name='efficience_calculee'),
        migrations.RemoveField(model_name='seguias', name='perte_infiltration_m3s'),
        migrations.RemoveField(model_name='seguias', name='perte_vaporisation_m3s'),
        migrations.RemoveField(model_name='seguias', name='date_dernier_calcul'),
        migrations.RemoveField(model_name='seguias', name='geometrie'),

        # ── 6. Retirer l'unicité de nom_de_la_seguia ─────────────────────────
        migrations.AlterField(
            model_name='seguias',
            name='nom_de_la_seguia',
            field=models.CharField(max_length=100),
        ),

        # ── 7. Supprimer EtatSeguia ───────────────────────────────────────────
        migrations.DeleteModel(name='EtatSeguia'),
    ]
