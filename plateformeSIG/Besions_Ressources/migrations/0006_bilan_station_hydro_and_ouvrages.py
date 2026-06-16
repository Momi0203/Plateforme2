from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0005_kc_kr_global_par_culture'),
        ('analyse_hydrologique', '0007_stationhydrometrique_annee_seche'),
        ('diagnostic', '0021_alter_assolement_culture'),
    ]

    operations = [
        migrations.AddField(
            model_name='bilanbesoinressources',
            name='station_hydrometrique',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='bilans_ressources',
                to='analyse_hydrologique.stationhydrometrique',
                verbose_name='Station hydrométrique',
            ),
        ),
        migrations.AlterField(
            model_name='bilanbesoinressources',
            name='canal_pente',
            field=models.FloatField(
                blank=True, null=True, default=0.0001,
                verbose_name='Pente canal (m/m)',
                help_text='Défaut : 0.0001 si non renseigné',
            ),
        ),
        migrations.AlterField(
            model_name='bilanbesoinressources',
            name='canal_manning_n',
            field=models.FloatField(
                default=0.015,
                verbose_name='Coefficient Manning n',
                help_text='Défaut : 0.015 si non renseigné',
            ),
        ),
        migrations.CreateModel(
            name='BilanOuvrageAssocie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_ouvrage', models.CharField(choices=[
                    ('seuil', 'Seuil'),
                    ('prise_locale', 'Prise locale'),
                    ('barrage', 'Barrage collinaire'),
                    ('khettara', 'Khettara'),
                    ('forage', 'Forage / Puits'),
                ], max_length=20)),
                ('tc_h', models.FloatField(blank=True, null=True, verbose_name='Tc (h)')),
                ('tc_source', models.CharField(blank=True, help_text="'analyse' ou 'moyenne'", max_length=20)),
                ('debit_troncon_m3s', models.FloatField(blank=True, null=True, verbose_name='Débit tronçon (m³/s)')),
                ('ordre', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bilan', models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name='ouvrages_associes',
                    to='Besions_Ressources.bilanbesoinressources',
                    verbose_name='Bilan',
                )),
                ('bassin_versant', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    related_name='bilans_ouvrages',
                    to='analyse_hydrologique.bassinversant',
                )),
                ('seuil', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.CASCADE,
                    related_name='bilans_associes',
                    to='diagnostic.seuil',
                )),
                ('prise_locale', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.CASCADE,
                    related_name='bilans_associes',
                    to='diagnostic.priselocale',
                )),
                ('barrage', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.CASCADE,
                    related_name='bilans_associes',
                    to='diagnostic.barrageretenue',
                )),
                ('khettara', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.CASCADE,
                    related_name='bilans_associes',
                    to='diagnostic.khettara',
                )),
                ('forage', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.CASCADE,
                    related_name='bilans_associes',
                    to='diagnostic.foragepuits',
                )),
                ('troncon_amenee', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    related_name='bilans_ouvrages',
                    to='diagnostic.seguias',
                    verbose_name="Tronçon d'amenée",
                )),
            ],
            options={
                'verbose_name': 'Ouvrage associé au bilan',
                'verbose_name_plural': 'Ouvrages associés au bilan',
                'ordering': ['ordre', 'id'],
            },
        ),
    ]
