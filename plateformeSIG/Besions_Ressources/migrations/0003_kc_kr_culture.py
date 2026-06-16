"""Refactor : remplacement de CulturePerimetre par Kc_Kr_culture.

CulturePerimetre était lié à Perimetre directement. Le nouveau modèle
Kc_Kr_culture est rattaché à `diagnostic.Assolement` (table enfant de
Perimetre) — donc enfant de l'enfant.

Migration en 3 phases :
1. Création de Kc_Kr_culture
2. RunPython qui copie chaque CulturePerimetre vers une nouvelle ligne
   Kc_Kr_culture en retrouvant (ou créant) un Assolement de même nom dans
   le périmètre source.
3. Suppression de CulturePerimetre.
"""
import django.db.models.deletion
from django.db import migrations, models


def migrate_cultures(apps, schema_editor):
    CulturePerimetre = apps.get_model('Besions_Ressources', 'CulturePerimetre')
    Kc_Kr_culture = apps.get_model('Besions_Ressources', 'Kc_Kr_culture')
    Assolement = apps.get_model('diagnostic', 'Assolement')

    for cp in CulturePerimetre.objects.all():
        # Retrouver ou créer un Assolement dans le périmètre portant le même nom
        assol = (Assolement.objects
                 .filter(perimetre=cp.perimetre, culture=cp.nom)
                 .first())
        if assol is None:
            assol = Assolement.objects.create(
                perimetre=cp.perimetre,
                culture=cp.nom or 'Culture',
                surface_ha=cp.superficie_ha,
                ordre=0,
            )
        Kc_Kr_culture.objects.create(
            nom=assol,
            superficie_ha=cp.superficie_ha,
            kc=cp.kc,
            kr=cp.kr,
        )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0002_remove_stationclimatique_perimetre_and_more'),
        ('diagnostic', '0014_perimetre_child_tables'),
    ]

    operations = [
        migrations.CreateModel(
            name='Kc_Kr_culture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('superficie_ha', models.FloatField(verbose_name='Superficie (ha)')),
                ('kc', models.JSONField(help_text='12 valeurs Sep→Aoû', verbose_name='Kc mensuel')),
                ('kr', models.JSONField(help_text='12 valeurs Sep→Aoû', verbose_name='Kr mensuel')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('nom', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='coefficients_kc_kr',
                    to='diagnostic.assolement',
                    verbose_name='Culture (assolement)',
                )),
            ],
            options={
                'verbose_name': "Kc/Kr d'une culture",
                'verbose_name_plural': 'Kc/Kr des cultures',
            },
        ),
        migrations.RunPython(migrate_cultures, reverse_noop),
        migrations.DeleteModel(name='CulturePerimetre'),
    ]
