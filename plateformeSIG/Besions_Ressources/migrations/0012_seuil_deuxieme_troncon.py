# Ajout d'un 2e tronçon d'amenée pour les seuils.
# Un seuil peut avoir 1 ou 2 tronçons d'amenée ; une prise locale en a 1.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0011_bilanbesoinressources_resultats_bilan_seche'),
        ('diagnostic', '0025_perimetre_et0_mm_jour_seguias_date_dernier_calcul_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='troncon_amenee_2',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='bilans_ouvrages_secondaire',
                to='diagnostic.seguias',
                verbose_name="Tronçon d'amenée (2)",
                help_text="2e tronçon d'amenée (seuil uniquement, optionnel)",
            ),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='debit_troncon_2_m3s',
            field=models.FloatField(
                blank=True, null=True,
                verbose_name='Débit tronçon 2 (m³/s)',
                help_text="Débit du 2e tronçon d'amenée (seuil uniquement)",
            ),
        ),
    ]
