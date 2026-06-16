"""
Migration 0014 : Repointe troncon_amenee et troncon_amenee_2 de Seguias → TronconSeguia.

Données migrées : pour chaque BilanOuvrageAssocie dont troncon_amenee (ou _2)
est renseigné, on recherche le premier TronconSeguia de cette séguia.
Si la séguia n'a pas de tronçon (cas théorique), on met NULL.
"""
import django.db.models.deletion
from django.db import migrations, models


def _migrer_troncon_amenee(apps, schema_editor):
    BilanOuvrageAssocie = apps.get_model('Besions_Ressources', 'BilanOuvrageAssocie')
    TronconSeguia = apps.get_model('diagnostic', 'TronconSeguia')

    for oa in BilanOuvrageAssocie.objects.all():
        # troncon_amenee
        old_id = oa.troncon_amenee_old_id
        if old_id:
            tr = TronconSeguia.objects.filter(seguia_id=old_id).first()
            oa.troncon_amenee_id = tr.pk if tr else None

        # troncon_amenee_2
        old_id_2 = oa.troncon_amenee_2_old_id
        if old_id_2:
            tr2 = TronconSeguia.objects.filter(seguia_id=old_id_2).first()
            oa.troncon_amenee_2_id = tr2.pk if tr2 else None

        oa.save(update_fields=['troncon_amenee_id', 'troncon_amenee_2_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0013_bilan_canal_forme_diametre'),
        ('diagnostic', '0028_troncon_statut'),
    ]

    operations = [
        # 1. Renommer les anciennes colonnes (garder les données existantes)
        migrations.RenameField(
            model_name='bilanouvrageassocie',
            old_name='troncon_amenee',
            new_name='troncon_amenee_old',
        ),
        migrations.RenameField(
            model_name='bilanouvrageassocie',
            old_name='troncon_amenee_2',
            new_name='troncon_amenee_2_old',
        ),

        # 2. Ajouter les nouvelles colonnes pointant vers TronconSeguia
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='troncon_amenee',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='bilans_ouvrages',
                to='diagnostic.tronconseguia',
                verbose_name="Tronçon d'amenée",
            ),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='troncon_amenee_2',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='bilans_ouvrages_secondaire',
                to='diagnostic.tronconseguia',
                verbose_name="Tronçon d'amenée (2)",
            ),
        ),

        # 3. Migrer les données
        migrations.RunPython(_migrer_troncon_amenee, migrations.RunPython.noop),

        # 4. Supprimer les anciennes colonnes
        migrations.RemoveField(model_name='bilanouvrageassocie', name='troncon_amenee_old'),
        migrations.RemoveField(model_name='bilanouvrageassocie', name='troncon_amenee_2_old'),
    ]
