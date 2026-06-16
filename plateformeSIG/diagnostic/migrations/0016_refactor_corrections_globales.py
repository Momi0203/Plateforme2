"""Refactor corrections globales :
- Suppression de OuvrageTeteAssocie (modèle remplacé par SguiaAssocie_OuvrageTete)
- Création de SguiaAssocie_OuvrageTete (liaison Séguia ↔ ouvrages de tête)
- Liaison Perimetre → carte.Commune
- Liaison BassinVersant → Seuil / PriseLocale / BarrageRetenue
- Champ efficience_reseaux (resp. efficience_trancons pour Seguias) sur les
  7 ouvrages de tête.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0015_alter_assolement_id_alter_organisationagriculteur_id_and_more'),
        ('carte', '0001_initial'),
        ('analyse_hydrologique', '0001_initial'),
    ]

    operations = [
        # ── Liaison Périmètre → Commune
        migrations.AddField(
            model_name='perimetre',
            name='commune',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='perimetres', to='carte.commune',
                verbose_name='Commune (entité)',
            ),
        ),

        # ── Champs efficience
        migrations.AddField(
            model_name='seuil', name='efficience_reseaux',
            field=models.FloatField(blank=True, help_text='Efficience du réseau (0–1)', null=True),
        ),
        migrations.AddField(
            model_name='murprotection', name='efficience_reseaux',
            field=models.FloatField(blank=True, help_text='Efficience du réseau (0–1)', null=True),
        ),
        migrations.AddField(
            model_name='seguias', name='efficience_trancons',
            field=models.FloatField(blank=True, help_text='Efficience des tronçons (0–1)', null=True),
        ),
        migrations.AddField(
            model_name='barrageretenue', name='efficience_reseaux',
            field=models.FloatField(blank=True, help_text='Efficience du réseau (0–1)', null=True),
        ),
        migrations.AddField(
            model_name='khettara', name='efficience_reseaux',
            field=models.FloatField(blank=True, help_text='Efficience du réseau (0–1)', null=True),
        ),
        migrations.AddField(
            model_name='foragepuits', name='efficience_reseaux',
            field=models.FloatField(blank=True, help_text='Efficience du réseau (0–1)', null=True),
        ),
        migrations.AddField(
            model_name='priselocale', name='efficience_reseaux',
            field=models.FloatField(blank=True, help_text='Efficience du réseau (0–1)', null=True),
        ),

        # ── Liaisons BassinVersant
        migrations.AddField(
            model_name='seuil', name='bassin_versant',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='seuils', to='analyse_hydrologique.bassinversant',
            ),
        ),
        migrations.AddField(
            model_name='priselocale', name='bassin_versant',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='prises_locales', to='analyse_hydrologique.bassinversant',
            ),
        ),
        migrations.AddField(
            model_name='barrageretenue', name='bassin_versant',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='barrages_retenue', to='analyse_hydrologique.bassinversant',
            ),
        ),

        # ── Création de la liaison N–N Séguia ↔ Ouvrages de tête
        migrations.CreateModel(
            name='SguiaAssocie_OuvrageTete',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('FK_nom_sguia', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ouvrages_tete_associes',
                    to='diagnostic.seguias',
                    verbose_name='Séguia',
                )),
                ('FK_seuil', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='seguias_associees',
                    to='diagnostic.seuil',
                )),
                ('FK_khettaras', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='seguias_associees',
                    to='diagnostic.khettara',
                )),
                ('FK_prise_locale', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='seguias_associees',
                    to='diagnostic.priselocale',
                )),
                ('FK_puit_forage', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='seguias_associees',
                    to='diagnostic.foragepuits',
                )),
                ('FK_barrage_retenue', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='seguias_associees',
                    to='diagnostic.barrageretenue',
                )),
            ],
            options={
                'verbose_name': 'Séguia / Ouvrage de tête (association)',
                'verbose_name_plural': 'Séguias / Ouvrages de tête (associations)',
            },
        ),

        # ── Suppression du modèle OuvrageTeteAssocie (devenu inutile)
        migrations.DeleteModel(name='OuvrageTeteAssocie'),
    ]
