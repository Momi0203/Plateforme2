"""Ajout du champ unite_rendement sur Assolement (qx/ha ou kg/arbre)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0018_merge_20260512_1058'),
    ]

    operations = [
        migrations.AddField(
            model_name='assolement',
            name='unite_rendement',
            field=models.CharField(
                max_length=20,
                choices=[('qx_ha', 'qx/ha'), ('kg_arbre', 'kg/arbre')],
                default='qx_ha',
                help_text="Unité du rendement",
            ),
        ),
    ]
