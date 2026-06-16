import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnostic', '0006_alter_priselocale_saisi_par_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Seuil : nom unique, géométrie optionnelle, coordonnées + nbr_pertuis
        migrations.AlterField(
            model_name='seuil',
            name='nom_du_seuil',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='seuil',
            name='localisation_du_seuil',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='seuil',
            name='geometrie',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='seuil',
            name='coordonnes_x',
            field=models.FloatField(blank=True, help_text='Coordonnée X (Nord Maroc, m)', null=True),
        ),
        migrations.AddField(
            model_name='seuil',
            name='coordonnes_y',
            field=models.FloatField(blank=True, help_text='Coordonnée Y (Nord Maroc, m)', null=True),
        ),
        migrations.AddField(
            model_name='seuil',
            name='nbr_pertuis_prise_droit',
            field=models.FloatField(blank=True, help_text="Prise d'eau rive droite - Nombre de pertuis", null=True),
        ),
        migrations.AddField(
            model_name='seuil',
            name='nbr_pertuis_prise_gauche',
            field=models.FloatField(blank=True, help_text="Prise d'eau rive gauche - Nombre de pertuis", null=True),
        ),
        migrations.AddField(
            model_name='seuil',
            name='nbr_pertuis_degrevement_droit',
            field=models.FloatField(blank=True, help_text='Passe de dégrèvement rive droite - Nombre de pertuis', null=True),
        ),
        migrations.AddField(
            model_name='seuil',
            name='nbr_pertuis_degrevement_gauche',
            field=models.FloatField(blank=True, help_text='Passe de dégrèvement rive gauche - Nombre de pertuis', null=True),
        ),
        migrations.AlterField(
            model_name='seuil',
            name='etat_construction_fonctionnement',
            field=models.TextField(blank=True, help_text='Texte libre (legacy — voir EtatSeuil)'),
        ),
        migrations.AlterField(
            model_name='seuil',
            name='etat_materiel_hydromecanique',
            field=models.CharField(blank=True, help_text='Texte legacy — voir EtatSeuil', max_length=500),
        ),

        # ── Nouveau modèle EtatSeuil
        migrations.CreateModel(
            name='EtatSeuil',
            fields=[
                ('seuil', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False,
                    related_name='diagnostic_etat',
                    to='diagnostic.seuil',
                )),
                ('date_diagnostic', models.DateField(default=django.utils.timezone.localdate)),
                ('etat_construction_fonctionnement', models.CharField(
                    blank=True, max_length=20,
                    choices=[
                        ('t_mauvais', 'Très mauvais'),
                        ('mauvais', 'Mauvais'),
                        ('moyen_mauvais', 'Moyen-mauvais'),
                        ('moyen', 'Moyen'),
                        ('moyen_bon', 'Moyen-bon'),
                        ('bon', 'Bon'),
                        ('excellent', 'Excellent'),
                    ],
                    verbose_name='État construction / fonctionnement',
                )),
                ('etat_materiel_hydromecanique', models.CharField(
                    blank=True, max_length=20,
                    choices=[
                        ('absence', 'Absence'),
                        ('t_mauvais', 'Très mauvais'),
                        ('mauvais', 'Mauvais'),
                        ('moyen_mauvais', 'Moyen-mauvais'),
                        ('moyen', 'Moyen'),
                        ('moyen_bon', 'Moyen-bon'),
                        ('bon', 'Bon'),
                        ('excellent', 'Excellent'),
                    ],
                    verbose_name='État matériel hydromécanique',
                )),
                ('etat_structurel_digue', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='État structurel de la digue')),
                ('affouillement_aval', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name="Affouillement à l'aval")),
                ('envasement_retenue', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='Envasement de la retenue')),
                ('murs_guideaux', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='Murs guideaux')),
                ('radier_aval', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='Radier aval')),
                ('etat_vannes', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='État des vannes')),
                ('dessableur', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='Dessableur')),
                ('degradation_beton', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='Dégradation du béton')),
                ('infiltration_fuite', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='Infiltration / fuite')),
                ('limiteur_debit', models.IntegerField(blank=True, choices=[(0, 'Absence / aucun problème'), (1, 'Très faible'), (2, 'Faible'), (3, 'Moyen'), (4, 'Dégradé'), (5, 'Grave / critique')], null=True, verbose_name='Limiteur de débit')),
                ('editeur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etat_seuils_edites',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'État de seuil (diagnostic)',
                'verbose_name_plural': 'États des seuils (diagnostics)',
            },
        ),
    ]
