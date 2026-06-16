# Bilan : champs par ouvrage (efficience, debit aval, capacite deversement,
# debits khettarat/transfert, tour eau, duree, coefficients, apports mensuels)
# + nouveau modele AutreRessource (parallele aux ouvrages associes).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Besions_Ressources', '0007_alter_bilanouvrageassocie_id'),
    ]

    operations = [
        # ── BilanOuvrageAssocie : champs communs ────────────────────────────────
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='efficience_reseau',
            field=models.FloatField(blank=True, null=True, verbose_name="Efficience du réseau (0–1)", help_text="Auto-rempli depuis l'ouvrage (défaut 0.75)"),
        ),
        # ── Seuil & Prise locale ───────────────────────────────────────────────
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='debit_aval_m3s',
            field=models.FloatField(blank=True, default=0.0, null=True, verbose_name="Débit prélevé en aval (m³/s)", help_text="Volume prélevé dans d'autres périmètres en aval (défaut 0)"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='capacite_deversement_pct',
            field=models.FloatField(blank=True, default=100.0, null=True, verbose_name="Capacité de déversement (%)", help_text="Dépend de l'angle de dérivation et de l'emplacement (défaut 100 %)"),
        ),
        # ── Khettara & Forage/Puits ────────────────────────────────────────────
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='debit_khettarat_m3s',
            field=models.FloatField(blank=True, null=True, verbose_name="Débit khettara (m³/s)"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='transfert_amont',
            field=models.BooleanField(default=False, verbose_name="Transfert amont activé"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='debit_transfert_m3s',
            field=models.FloatField(blank=True, null=True, verbose_name="Débit de transfert (m³/s)"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='tour_eau_jours',
            field=models.FloatField(blank=True, default=1.0, null=True, verbose_name="Tour d'eau (jours)"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='duree_jours',
            field=models.FloatField(blank=True, default=30.5, null=True, verbose_name="Durée (jours)"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='coeff_humide',
            field=models.FloatField(blank=True, default=1.30, null=True, verbose_name="Coefficient d'humidité"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='coeff_seche',
            field=models.FloatField(blank=True, default=0.80, null=True, verbose_name="Coefficient de sécheresse"),
        ),
        # ── Barrage : apports mensuels 3 années ───────────────────────────────
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='apports_mensuels_normale',
            field=models.JSONField(blank=True, null=True, verbose_name="Apports mensuels année normale (m³/s, Sep→Aoû)"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='apports_mensuels_humide',
            field=models.JSONField(blank=True, null=True, verbose_name="Apports mensuels année humide (m³/s, Sep→Aoû)"),
        ),
        migrations.AddField(
            model_name='bilanouvrageassocie',
            name='apports_mensuels_seche',
            field=models.JSONField(blank=True, null=True, verbose_name="Apports mensuels année sèche (m³/s, Sep→Aoû)"),
        ),
        # ── Nouveau modèle AutreRessource ──────────────────────────────────────
        migrations.CreateModel(
            name='AutreRessource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=150, verbose_name='Nom de la ressource')),
                ('apports_mensuels_normale', models.JSONField(blank=True, null=True, verbose_name='Apports mensuels année normale (m³/s, Sep→Aoû)')),
                ('apports_mensuels_humide', models.JSONField(blank=True, null=True, verbose_name='Apports mensuels année humide (m³/s, Sep→Aoû)')),
                ('apports_mensuels_seche', models.JSONField(blank=True, null=True, verbose_name='Apports mensuels année sèche (m³/s, Sep→Aoû)')),
                ('efficience', models.FloatField(default=0.80, help_text='Défaut 0.80 (80 %)', verbose_name='Efficience (0–1)')),
                ('ordre', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bilan', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='autres_ressources_eau', to='Besions_Ressources.bilanbesoinressources', verbose_name='Bilan')),
            ],
            options={
                'verbose_name': 'Autre ressource',
                'verbose_name_plural': 'Autres ressources',
                'ordering': ['ordre', 'id'],
            },
        ),
    ]
