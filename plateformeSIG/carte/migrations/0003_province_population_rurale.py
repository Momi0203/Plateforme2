from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carte', '0002_alter_commune_id_alter_province_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='province',
            name='population_rurale',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
