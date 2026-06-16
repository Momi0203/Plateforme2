from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0021_alter_assolement_culture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seguias',
            name='debit',
            field=models.FloatField(
                verbose_name='Débit (m³/s)',
                help_text='Débit transitant dans le tronçon en m³/s',
            ),
        ),
    ]
