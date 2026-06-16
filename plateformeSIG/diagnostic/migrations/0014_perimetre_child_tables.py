"""Suppression du stockage par séparateur sur Perimetre :
- Les listes JSON cultures/pourcentage/rendement → table enfant Assolement
- ayants_droit_eau/cycle_tour_eau_jours/duree_tour_eau_heures → TourEau
- organisations_agriculteurs → OrganisationAgriculteur
- ouvrages_en_tete_associes → OuvrageTeteAssocie
- statut_juridique (liste) → 5 colonnes fixes (melk/collectif/location/guiche/habousse)
"""
import django.db.models.deletion
from django.db import migrations, models


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def migrate_to_child_tables(apps, schema_editor):
    Perimetre = apps.get_model('diagnostic', 'Perimetre')
    Assolement = apps.get_model('diagnostic', 'Assolement')
    TourEau = apps.get_model('diagnostic', 'TourEau')
    OrganisationAgriculteur = apps.get_model('diagnostic', 'OrganisationAgriculteur')
    OuvrageTeteAssocie = apps.get_model('diagnostic', 'OuvrageTeteAssocie')

    for p in Perimetre.objects.all():
        # ── Statut juridique : liste ordonnée → 5 colonnes
        sj = p.statut_juridique or []
        keys = ['statut_juridique_melk', 'statut_juridique_collectif',
                'statut_juridique_location', 'statut_juridique_guiche',
                'statut_juridique_habousse']
        for i, k in enumerate(keys):
            if i < len(sj):
                setattr(p, k, _to_float(sj[i]))
        p.save(update_fields=keys)

        # ── Assolement : 3 listes parallèles → N lignes
        cults = p.cultures or []
        pcts = p.pourcentage_cultures or []
        rdts = p.rendement_cultures or []
        n = max(len(cults), len(pcts), len(rdts))
        for i in range(n):
            culture = (cults[i] if i < len(cults) else '') or ''
            culture = str(culture).strip()
            if not culture:
                continue
            Assolement.objects.create(
                perimetre=p,
                culture=culture,
                pourcentage=_to_float(pcts[i]) if i < len(pcts) else None,
                rendement=_to_float(rdts[i]) if i < len(rdts) else None,
                ordre=i,
            )

        # ── Tour d'eau : 3 listes parallèles → N lignes
        ayants = p.ayants_droit_eau or []
        cycs = p.cycle_tour_eau_jours or []
        durs = p.duree_tour_eau_heures or []
        n = max(len(ayants), len(cycs), len(durs))
        for i in range(n):
            ayant = (ayants[i] if i < len(ayants) else '') or ''
            ayant = str(ayant).strip()
            if not ayant:
                continue
            TourEau.objects.create(
                perimetre=p,
                ayant_droit=ayant,
                cycle_jours=_to_float(cycs[i]) if i < len(cycs) else None,
                duree_heures=_to_float(durs[i]) if i < len(durs) else None,
                ordre=i,
            )

        # ── Organisations d'agriculteurs
        for i, nom in enumerate(p.organisations_agriculteurs or []):
            nom = str(nom).strip()
            if nom:
                OrganisationAgriculteur.objects.create(perimetre=p, nom=nom, ordre=i)

        # ── Ouvrages en tête associés (texte libre)
        for i, nom in enumerate(p.ouvrages_en_tete_associes or []):
            nom = str(nom).strip()
            if nom:
                OuvrageTeteAssocie.objects.create(perimetre=p, nom=nom, ordre=i)


def reverse_noop(apps, schema_editor):
    """Pas de retour arrière automatique : les données sont préservées dans les
    tables enfants ; recréer les listes JSON nécessiterait de reconstituer
    l'ordre — déconseillé."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0013_prise_diagnostic_structure'),
    ]

    operations = [
        # ── 1. Création des 4 tables enfants + 5 colonnes statut juridique
        migrations.AddField(
            model_name='perimetre',
            name='statut_juridique_melk',
            field=models.FloatField(blank=True, help_text='% melk', null=True),
        ),
        migrations.AddField(
            model_name='perimetre',
            name='statut_juridique_collectif',
            field=models.FloatField(blank=True, help_text='% collectif', null=True),
        ),
        migrations.AddField(
            model_name='perimetre',
            name='statut_juridique_location',
            field=models.FloatField(blank=True, help_text='% location', null=True),
        ),
        migrations.AddField(
            model_name='perimetre',
            name='statut_juridique_guiche',
            field=models.FloatField(blank=True, help_text='% guich', null=True),
        ),
        migrations.AddField(
            model_name='perimetre',
            name='statut_juridique_habousse',
            field=models.FloatField(blank=True, help_text='% habous', null=True),
        ),
        migrations.CreateModel(
            name='Assolement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('culture', models.CharField(max_length=100)),
                ('pourcentage', models.FloatField(blank=True, help_text='% de la surface cultivée', null=True)),
                ('surface_ha', models.FloatField(blank=True, help_text='Surface (ha)', null=True)),
                ('rendement', models.FloatField(blank=True, help_text='Rendement (qx/ha)', null=True)),
                ('ordre', models.PositiveSmallIntegerField(default=0)),
                ('perimetre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assolement', to='diagnostic.perimetre')),
            ],
            options={'verbose_name': 'Assolement', 'verbose_name_plural': 'Assolements', 'ordering': ['ordre', 'id']},
        ),
        migrations.CreateModel(
            name='TourEau',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ayant_droit', models.CharField(help_text='Famille / ayant droit', max_length=200)),
                ('cycle_jours', models.FloatField(blank=True, null=True)),
                ('duree_heures', models.FloatField(blank=True, null=True)),
                ('ordre', models.PositiveSmallIntegerField(default=0)),
                ('perimetre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tours_eau', to='diagnostic.perimetre')),
            ],
            options={"verbose_name": "Tour d'eau", "verbose_name_plural": "Tours d'eau", 'ordering': ['ordre', 'id']},
        ),
        migrations.CreateModel(
            name='OrganisationAgriculteur',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('ordre', models.PositiveSmallIntegerField(default=0)),
                ('perimetre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organisations', to='diagnostic.perimetre')),
            ],
            options={"verbose_name": "Organisation d'agriculteurs", "verbose_name_plural": "Organisations d'agriculteurs", 'ordering': ['ordre', 'id']},
        ),
        migrations.CreateModel(
            name='OuvrageTeteAssocie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('ordre', models.PositiveSmallIntegerField(default=0)),
                ('perimetre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ouvrages_associes', to='diagnostic.perimetre')),
            ],
            options={'verbose_name': 'Ouvrage en tête associé', 'verbose_name_plural': 'Ouvrages en tête associés', 'ordering': ['ordre', 'id']},
        ),

        # ── 2. Migration des données depuis les anciens JSONField
        migrations.RunPython(migrate_to_child_tables, reverse_noop),

        # ── 3. Suppression des JSONField devenus inutiles
        migrations.RemoveField(model_name='perimetre', name='statut_juridique'),
        migrations.RemoveField(model_name='perimetre', name='cultures'),
        migrations.RemoveField(model_name='perimetre', name='pourcentage_cultures'),
        migrations.RemoveField(model_name='perimetre', name='rendement_cultures'),
        migrations.RemoveField(model_name='perimetre', name='ayants_droit_eau'),
        migrations.RemoveField(model_name='perimetre', name='cycle_tour_eau_jours'),
        migrations.RemoveField(model_name='perimetre', name='duree_tour_eau_heures'),
        migrations.RemoveField(model_name='perimetre', name='organisations_agriculteurs'),
        migrations.RemoveField(model_name='perimetre', name='ouvrages_en_tete_associes'),
    ]
