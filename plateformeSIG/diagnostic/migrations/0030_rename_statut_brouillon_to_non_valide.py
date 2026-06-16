from django.db import migrations


def rename_brouillon_to_non_valide(apps, schema_editor):
    models_fields = [
        ('Perimetre',      'statut'),
        ('Seuil',          'statut'),
        ('MurProtection',  'statut'),
        ('BarrageRetenue', 'statut'),
        ('Khettara',       'statut'),
        ('ForagePuits',    'statut'),
        ('PriseLocale',    'statut'),
        ('TronconSeguia',  'statut'),
    ]
    for model_name, field in models_fields:
        Model = apps.get_model('diagnostic', model_name)
        Model.objects.filter(**{field: 'brouillon'}).update(**{field: 'non_valide'})


def revert_non_valide_to_brouillon(apps, schema_editor):
    models_fields = [
        ('Perimetre',      'statut'),
        ('Seuil',          'statut'),
        ('MurProtection',  'statut'),
        ('BarrageRetenue', 'statut'),
        ('Khettara',       'statut'),
        ('ForagePuits',    'statut'),
        ('PriseLocale',    'statut'),
        ('TronconSeguia',  'statut'),
    ]
    for model_name, field in models_fields:
        Model = apps.get_model('diagnostic', model_name)
        Model.objects.filter(**{field: 'non_valide'}).update(**{field: 'brouillon'})


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0029_alter_tronconseguia_diametre_alter_tronconseguia_id'),
    ]

    operations = [
        migrations.RunPython(
            rename_brouillon_to_non_valide,
            reverse_code=revert_non_valide_to_brouillon,
        ),
    ]
