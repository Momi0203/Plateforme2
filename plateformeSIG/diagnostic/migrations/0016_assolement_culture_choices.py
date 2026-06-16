"""Contraint Assolement.culture au référentiel CULTURES_TAFILALET (choices).

Modification de schéma uniquement (max_length inchangé) — les valeurs
existantes hors référentiel ne sont pas validées par la DB mais le seront
par les formulaires (et le validateur Django sur clean()).
"""
from django.db import migrations, models


CULTURES_TAFILALET = [
    ("Abricot", "Abricot"), ("Agrumes", "Agrumes"), ("Amande", "Amande"),
    ("Betterave", "Betterave"), ("Blé", "Blé"), ("Carotte", "Carotte"),
    ("Citron", "Citron"), ("Clémentine", "Clémentine"), ("Cumin", "Cumin"),
    ("Datte", "Datte"), ("Figue", "Figue"), ("Grenade", "Grenade"),
    ("Luzerne", "Luzerne"), ("Mandarine", "Mandarine"), ("Menthe", "Menthe"),
    ("Mûre", "Mûre"), ("Noix", "Noix"), ("Oignon", "Oignon"),
    ("Olive", "Olive"), ("Orange", "Orange"), ("Orge", "Orge"),
    ("Pastèque", "Pastèque"), ("Piment", "Piment"), ("Pois", "Pois"),
    ("Pomme", "Pomme"), ("PommeTerre", "Pomme de terre"), ("Raisin", "Raisin"),
    ("Rose", "Rose"), ("Safran", "Safran"), ("Tomate", "Tomate"),
]


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0016_refactor_corrections_globales'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assolement',
            name='culture',
            field=models.CharField(choices=CULTURES_TAFILALET, max_length=100),
        ),
    ]
