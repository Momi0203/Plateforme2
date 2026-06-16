"""
Migration 0028 : Déplace le champ statut de Seguias vers TronconSeguia.
"""
from django.db import migrations, models


def _copier_statut_seguia_vers_troncons(apps, schema_editor):
    """Chaque tronçon hérite du statut de sa séguia parente."""
    TronconSeguia = apps.get_model('diagnostic', 'TronconSeguia')
    for tr in TronconSeguia.objects.select_related('seguia').all():
        tr.statut = getattr(tr.seguia, 'statut', 'brouillon') or 'brouillon'
        tr.save(update_fields=['statut'])


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0027_troncon_seguia_refactor'),
    ]

    operations = [
        # 1. Ajouter statut sur TronconSeguia (temporairement nullable)
        migrations.AddField(
            model_name='tronconseguia',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
            ),
        ),

        # 2. Copier le statut de chaque séguia vers ses tronçons
        migrations.RunPython(_copier_statut_seguia_vers_troncons, migrations.RunPython.noop),

        # 3. Supprimer statut de Seguias
        migrations.RemoveField(model_name='seguias', name='statut'),
    ]
