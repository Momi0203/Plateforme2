from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0015_alter_bilanouvrageassocie_troncon_amenee_2'),
    ]

    operations = [
        migrations.AddField(
            model_name='bilanbesoinressources',
            name='est_valide',
            field=models.BooleanField(default=False, verbose_name='Bilan validé'),
        ),
    ]
