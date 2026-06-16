from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyse_hydrologique', '0010_alter_stationhydrometrique_frequences_mensuelles_annee_humide_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultatanalysehydrologique',
            name='statut',
            field=models.CharField(
                choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
                default='brouillon',
                max_length=20,
                verbose_name='Statut',
            ),
        ),
    ]
