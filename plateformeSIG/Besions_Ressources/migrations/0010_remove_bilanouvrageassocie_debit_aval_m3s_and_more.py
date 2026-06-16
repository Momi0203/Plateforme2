# Correction terminologique : debit_aval_m3s -> debit_amont_m3s (sans changer
# la formule de calcul). RenameField pour preserver les donnees existantes.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0009_alter_autreressource_apports_mensuels_humide_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bilanouvrageassocie',
            old_name='debit_aval_m3s',
            new_name='debit_amont_m3s',
        ),
        migrations.AlterField(
            model_name='bilanouvrageassocie',
            name='debit_amont_m3s',
            field=models.FloatField(
                blank=True, default=0.0, null=True,
                help_text="Volume prélevé dans d'autres périmètres en amont (défaut 0)",
                verbose_name="Débit prélevé en amont (m³/s)",
            ),
        ),
    ]
