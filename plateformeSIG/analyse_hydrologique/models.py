from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings


class BassinVersant(models.Model):
    nom = models.CharField(max_length=255)
    x_exutoire = models.FloatField(verbose_name="X exutoire (Nord Maroc, m)")
    y_exutoire = models.FloatField(verbose_name="Y exutoire (Nord Maroc, m)")
    surface = models.FloatField(verbose_name="Surface (km²)")
    perimetre = models.FloatField(verbose_name="Périmètre (km)")
    z_min = models.FloatField(verbose_name="Zmin (m)")
    z_max = models.FloatField(verbose_name="Zmax (m)")
    thalweg = models.FloatField(verbose_name="Longueur du thalweg (km)")
    ouvrage_en_tete = models.CharField(max_length=255, blank=True, verbose_name="Ouvrage en tête")
    geometrie = gis_models.PolygonField(srid=4326, null=True, blank=True, verbose_name="Géométrie")

    class Meta:
        verbose_name = "Bassin Versant"
        verbose_name_plural = "Bassins Versants"

    def __str__(self):
        return self.nom


class StationPluviometrique(models.Model):
    nom = models.CharField(max_length=255)
    x = models.FloatField(verbose_name="X (Nord Maroc, m)")
    y = models.FloatField(verbose_name="Y (Nord Maroc, m)")
    # Séries temporelles (une valeur par année)
    annees = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
        verbose_name="Années"
    )
    pjmax = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        verbose_name="Pjmax observées (mm)"
    )
    # Pjmax pour chaque période de retour
    pjmax_t10 = models.FloatField(null=True, blank=True, verbose_name="Pjmax T=10 ans (mm)")
    pjmax_t20 = models.FloatField(null=True, blank=True, verbose_name="Pjmax T=20 ans (mm)")
    pjmax_t50 = models.FloatField(null=True, blank=True, verbose_name="Pjmax T=50 ans (mm)")
    pjmax_t100 = models.FloatField(null=True, blank=True, verbose_name="Pjmax T=100 ans (mm)")
    hauteur_moyenne = models.FloatField(verbose_name="Hauteur moyenne annuelle (mm)")
    grad_exp_pluie = models.FloatField(verbose_name="Gradient exponentiel de pluie")
    # Polygone (zone d'influence / Thiessen)
    geometrie = gis_models.PolygonField(srid=4326, null=True, blank=True, verbose_name="Géométrie (polygone)")
    # Point de localisation (x/y sont en WGS84 degrés, pas en Lambert Nord Maroc)
    geom_point = gis_models.PointField(srid=4326, null=True, blank=True, verbose_name="Géométrie point (WGS84)")

    class Meta:
        verbose_name = "Station Pluviométrique"
        verbose_name_plural = "Stations Pluviométriques"

    def __str__(self):
        return self.nom


class StationHydrometrique(models.Model):
    nom = models.CharField(max_length=255)
    x = models.FloatField(verbose_name="X (Nord Maroc, m)")
    y = models.FloatField(verbose_name="Y (Nord Maroc, m)")
    # Séries temporelles (une valeur par année)
    annees = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
        verbose_name="Années"
    )
    qjmax = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        verbose_name="Qjmax observées (m³/s)"
    )
    # Qjmax pour chaque période de retour
    qjmax_t10 = models.FloatField(null=True, blank=True, verbose_name="Qjmax T=10 ans (m³/s)")
    qjmax_t20 = models.FloatField(null=True, blank=True, verbose_name="Qjmax T=20 ans (m³/s)")
    qjmax_t50 = models.FloatField(null=True, blank=True, verbose_name="Qjmax T=50 ans (m³/s)")
    qjmax_t100 = models.FloatField(null=True, blank=True, verbose_name="Qjmax T=100 ans (m³/s)")
    superficie_bv_jaugee = models.FloatField(null=True, blank=True, verbose_name="Superficie BV jaugé (km²)")
    # Débits mensuels observés pour l'année humide de référence (Sep → Aoû, 12 valeurs)
    debits_mensuels_annee_humide = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        size=12,
        verbose_name="Débits mensuels année humide (m³/s, Sep→Aoû)"
    )
    debits_mensuels_annee_normale = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        size=12,
        verbose_name="Débits mensuels année normale (m³/s, Sep→Aoû)"
    )
    debits_mensuels_annee_seche = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        size=12,
        verbose_name="Débits mensuels année sèche (m³/s, Sep→Aoû)"
    )
    frequences_mensuelles_annee_normale = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        size=12,
        verbose_name="Fréquences mensuelles année normale (jours, Sep→Aoû)"
    )
    frequences_mensuelles_annee_humide = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        size=12,
        verbose_name="Fréquences mensuelles année humide (jours, Sep→Aoû)"
    )
    frequences_mensuelles_annee_seche = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        size=12,
        verbose_name="Fréquences mensuelles année sèche (jours, Sep→Aoû)"
    )
    geometrie = gis_models.PointField(srid=4326, null=True, blank=True, verbose_name="Géométrie (point)")

    class Meta:
        verbose_name = "Station Hydrométrique"
        verbose_name_plural = "Stations Hydrométriques"

    def __str__(self):
        return self.nom


class CoefficientMontana(models.Model):
    station = models.OneToOneField(
        StationPluviometrique,
        on_delete=models.CASCADE,
        related_name="coefficients_montana",
        verbose_name="Station pluviométrique"
    )
    # Coefficients a par période de retour
    a10  = models.FloatField(null=True, blank=True, verbose_name="a  T=10 ans")
    a20  = models.FloatField(null=True, blank=True, verbose_name="a  T=20 ans")
    a50  = models.FloatField(null=True, blank=True, verbose_name="a  T=50 ans")
    a100 = models.FloatField(null=True, blank=True, verbose_name="a  T=100 ans")
    # Coefficients b par période de retour
    b10  = models.FloatField(null=True, blank=True, verbose_name="b  T=10 ans")
    b20  = models.FloatField(null=True, blank=True, verbose_name="b  T=20 ans")
    b50  = models.FloatField(null=True, blank=True, verbose_name="b  T=50 ans")
    b100 = models.FloatField(null=True, blank=True, verbose_name="b  T=100 ans")

    class Meta:
        verbose_name = "Coefficient de Montana"
        verbose_name_plural = "Coefficients de Montana"

    def __str__(self):
        return f"Montana — {self.station.nom}"


class ResultatAnalyseHydrologique(models.Model):
    METHODE_CHOICES = [
        ("rationnelle",  "Méthode Rationnelle"),
        ("socose",       "Méthode SOCOSE"),
        ("montana",      "Formule de Montana"),
        ("gradex",       "Méthode du Gradex"),
        ("autre",        "Autre"),
    ]

    operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="analyses_hydrologiques",
        verbose_name="Opérateur"
    )
    bassin_versant = models.ForeignKey(
        BassinVersant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resultats_analyse",
        verbose_name="Bassin versant"
    )
    date_analyse = models.DateTimeField(auto_now_add=True, verbose_name="Date d'analyse")
    methode = models.CharField(
        max_length=50,
        choices=METHODE_CHOICES,
        blank=True,
        verbose_name="Méthode utilisée"
    )
    # Débits de crue calculés (m³/s)
    qcrue_t10  = models.FloatField(null=True, blank=True, verbose_name="Q crue T=10 ans (m³/s)")
    qcrue_t20  = models.FloatField(null=True, blank=True, verbose_name="Q crue T=20 ans (m³/s)")
    qcrue_t50  = models.FloatField(null=True, blank=True, verbose_name="Q crue T=50 ans (m³/s)")
    qcrue_t100 = models.FloatField(null=True, blank=True, verbose_name="Q crue T=100 ans (m³/s)")
    # Paramètres intermédiaires
    temps_concentration = models.FloatField(null=True, blank=True, verbose_name="Temps de concentration (h)")
    coefficient_ruissellement = models.FloatField(null=True, blank=True, verbose_name="Coefficient de ruissellement")
    # Observations et conclusions libres
    observations    = models.TextField(blank=True, verbose_name="Observations")
    conclusions     = models.TextField(blank=True, verbose_name="Conclusions et recommandations")
    details_calcul  = models.JSONField(null=True, blank=True, verbose_name="Détails de calcul (JSON)")
    statut = models.CharField(
        max_length=20,
        choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
        default='brouillon',
        verbose_name="Statut",
    )

    class Meta:
        verbose_name = "Résultat d'Analyse Hydrologique"
        verbose_name_plural = "Résultats d'Analyses Hydrologiques"
        ordering = ["-date_analyse"]

    def __str__(self):
        date = self.date_analyse.strftime("%d/%m/%Y") if self.date_analyse else "—"
        bv = self.bassin_versant.nom if self.bassin_versant else "—"
        return f"Analyse [{bv}] par {self.operateur} le {date}"
