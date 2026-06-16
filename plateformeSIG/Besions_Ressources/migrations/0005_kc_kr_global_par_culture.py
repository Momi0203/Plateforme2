"""Kc_Kr_culture devient un référentiel global par nom de culture.

Avant : `nom = FK(Assolement)` + `superficie_ha` → 1 ligne par couple
        (périmètre, culture).
Après : `nom = CharField(unique, choices)` → 1 seule ligne par culture
        (les Kc/Kr sont identiques pour tous les périmètres).

Migration en 4 phases :
1. Ajout d'une colonne temporaire `nom_tmp` (CharField nullable).
2. RunPython : pour chaque ligne existante, lire le nom de culture via la FK
   Assolement et le copier dans `nom_tmp` ; dédoublonner en supprimant les
   doublons (on garde le plus récent).
3. Drop de la FK `nom` et de `superficie_ha` ; renommage `nom_tmp` → `nom` ;
   ajout des contraintes choices/unique.
4. (`updated_at` ajouté en passant.)
"""
from django.db import migrations, models


def copy_culture_name(apps, schema_editor):
    Kc = apps.get_model('Besions_Ressources', 'Kc_Kr_culture')
    seen = set()
    # On itère par PK décroissant pour garder la ligne la plus récente en cas
    # de doublon de nom (et supprimer les anciennes).
    for row in Kc.objects.order_by('-pk').select_related('nom'):
        culture_name = row.nom.culture if row.nom_id else None
        if not culture_name or culture_name in seen:
            row.delete()
            continue
        seen.add(culture_name)
        row.nom_tmp = culture_name
        row.save(update_fields=['nom_tmp'])


def reverse_noop(apps, schema_editor):
    pass


CULTURES_TAFILALET = [
    ("Abricot", "Abricot"), ("Agrumes", "Agrumes"), ("Amande", "Amande"),
    ("Betterave", "Betterave"), ("Blé", "Blé"), ("Carotte", "Carotte"),
    ("Citron", "Citron"), ("Clémentine", "Clémentine"), ("Cumin", "Cumin"),
    ("Datte", "Datte"), ("Figue", "Figue"), ("Grenade", "Grenade"),
    ("Luzerne", "Luzerne"), ("Mandarine", "Mandarine"), ("Menthe", "Menthe"),
    ("Mûre", "Mûre"), ("Noix", "Noix"), ("Oignon", "Oignon"),
    ("Olive", "Olive"), ("Orange", "Orange"), ("Orge", "Orge"),
    ("Pastèque", "Pastèque"), ("Peche", "Peche"), ("Piment", "Piment"),
    ("Pois", "Pois"), ("Pomme", "Pomme"), ("PommeTerre", "Pomme de terre"),
    ("Raisin", "Raisin"), ("Rose", "Rose"), ("Safran", "Safran"),
    ("Tomate", "Tomate"),
]


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0004_alter_kc_kr_culture_id'),
        ('diagnostic', '0019_assolement_unite_rendement'),
    ]

    operations = [
        # 1. Colonne temporaire
        migrations.AddField(
            model_name='kc_kr_culture',
            name='nom_tmp',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        # 2. Copie des noms depuis l'Assolement référencé
        migrations.RunPython(copy_culture_name, reverse_noop),

        # 3. Suppression de l'ancienne FK + superficie_ha
        migrations.RemoveField(model_name='kc_kr_culture', name='nom'),
        migrations.RemoveField(model_name='kc_kr_culture', name='superficie_ha'),

        # 4. Renommage temporaire → nom + ajout updated_at
        migrations.RenameField(
            model_name='kc_kr_culture',
            old_name='nom_tmp',
            new_name='nom',
        ),
        migrations.AlterField(
            model_name='kc_kr_culture',
            name='nom',
            field=models.CharField(
                max_length=100, unique=True,
                choices=CULTURES_TAFILALET,
                verbose_name='Nom de culture',
            ),
        ),
        migrations.AddField(
            model_name='kc_kr_culture',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterModelOptions(
            name='kc_kr_culture',
            options={
                'verbose_name': "Kc/Kr d'une culture",
                'verbose_name_plural': 'Kc/Kr des cultures',
                'ordering': ['nom'],
            },
        ),
    ]
