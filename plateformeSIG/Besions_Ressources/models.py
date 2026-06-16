from django.db import models
from django.contrib.gis.db import models as gis_models


class StationClimatique(models.Model):
    """Station climatique avec données mensuelles (Sep → Aoû)."""

    nom = models.CharField(max_length=100, verbose_name="Nom de la station")
    latitude = models.FloatField(verbose_name="Latitude (degrés)")
    x = models.FloatField(null=True, blank=True, verbose_name="X (Nord Maroc, m)")
    y = models.FloatField(null=True, blank=True, verbose_name="Y (Nord Maroc, m)")
    # 12 valeurs mensuelles Sep→Aoû
    temperatures_moyennes = models.JSONField(
        verbose_name="Températures moyennes (°C)",
        help_text="12 valeurs Sep→Aoû",
    )
    taux_insolation = models.JSONField(
        verbose_name="Taux d'insolation n/N",
        help_text="12 valeurs Sep→Aoû (0–1)",
    )
    precipitations_normales = models.JSONField(
        verbose_name="Précipitations année normale (mm/mois)",
        help_text="12 valeurs Sep→Aoû",
    )
    precipitations_humides = models.JSONField(
        verbose_name="Précipitations année humide (mm/mois)",
        help_text="12 valeurs Sep→Aoû",
        null=True, blank=True,
    )
    geometrie = gis_models.PointField(
        srid=4326,
        null=True, blank=True,
        verbose_name="Géométrie (point)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Station Climatique"
        verbose_name_plural = "Stations Climatiques"

    def __str__(self):
        return self.nom


class Kc_Kr_culture(models.Model):
    """Coefficients culturaux Kc/Kr — **référentiel global par nom de culture**.

    Un seul enregistrement par nom de culture (clé unique). Les coefficients
    Kc/Kr sont les mêmes pour tous les périmètres : la surface utilisée par
    les calculs de bilan provient de l'Assolement du périmètre considéré.
    """

    from diagnostic.models import CULTURES_TAFILALET as _CHOICES

    nom = models.CharField(
        max_length=100,
        unique=True,
        choices=_CHOICES,
        verbose_name="Nom de culture",
    )
    kc = models.JSONField(verbose_name="Kc mensuel", help_text="12 valeurs Sep→Aoû")
    kr = models.JSONField(verbose_name="Kr mensuel", help_text="12 valeurs Sep→Aoû")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kc/Kr d'une culture"
        verbose_name_plural = "Kc/Kr des cultures"
        ordering = ['nom']

    def __str__(self):
        return f"Kc/Kr — {self.get_nom_display()}"


class BilanBesoinRessources(models.Model):
    """Bilan besoin-ressources en eau pour un périmètre."""

    perimetre = models.ForeignKey(
        'diagnostic.Perimetre',
        on_delete=models.CASCADE,
        related_name='bilans_ressources',
        verbose_name="Périmètre",
    )
    station_climatique = models.ForeignKey(
        StationClimatique,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Station climatique",
    )
    station_hydrometrique = models.ForeignKey(
        'analyse_hydrologique.StationHydrometrique',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='bilans_ressources',
        verbose_name="Station hydrométrique",
    )
    efficiance_reseau = models.FloatField(
        default=0.9,
        verbose_name="Efficiance du réseau (0–1)",
    )

    # ── Paramètres hydrauliques pour les crues ────────────────────────────────
    # Dérivés des ouvrages associés (snapshot au moment du calcul)
    bassin_versant = models.ForeignKey(
        'analyse_hydrologique.BassinVersant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Bassin versant",
    )
    debits_mensuels_m3s = models.JSONField(
        null=True, blank=True,
        verbose_name="Débits mensuels station (m³/s)",
        help_text="12 valeurs Sep→Aoû",
    )
    superficie_bv_jaugee_km2 = models.FloatField(
        null=True, blank=True,
        verbose_name="Superficie BV jaugé (km²)",
    )
    tc_h = models.FloatField(
        null=True, blank=True,
        verbose_name="Temps de concentration (h)",
    )

    # ── Dimensions du canal principal ─────────────────────────────────────────
    # Une séguia peut être trapezoïdale, rectangulaire ou circulaire. La forme
    # détermine quels champs sont utilisés : trap/rect → b, y, z ; circ → diametre, y.
    CANAL_FORME_CHOICES = [
        ('trapezoidale',  'Trapézoïdale'),
        ('rectangulaire', 'Rectangulaire'),
        ('circulaire',    'Circulaire'),
    ]
    canal_forme = models.CharField(
        max_length=20,
        choices=CANAL_FORME_CHOICES,
        default='trapezoidale',
        verbose_name="Forme de section",
    )
    canal_b = models.FloatField(null=True, blank=True, verbose_name="Largeur fond canal b (m)")
    canal_y = models.FloatField(null=True, blank=True, verbose_name="Hauteur eau canal y (m)")
    canal_z = models.FloatField(null=True, blank=True, verbose_name="Fruit de berge z")
    canal_diametre = models.FloatField(
        null=True, blank=True,
        verbose_name="Diamètre canal (m)",
        help_text="Requis si forme circulaire",
    )
    canal_pente = models.FloatField(
        null=True, blank=True,
        default=0.0001,
        verbose_name="Pente canal (m/m)",
        help_text="Défaut : 0.0001 si non renseigné",
    )
    canal_manning_n = models.FloatField(
        default=0.015,
        verbose_name="Coefficient Manning n",
        help_text="Défaut : 0.015 si non renseigné",
    )
    coeff_humide = models.FloatField(default=1.30, verbose_name="Coefficient année humide")

    # ── Autres ressources (JSON) ───────────────────────────────────────────────
    # Exemple : [{"type":"puits","nom":"F1","debit_m3h":15,"heures_j":8}, ...]
    autres_ressources = models.JSONField(null=True, blank=True, verbose_name="Autres ressources")

    # ── Résultats calculés ────────────────────────────────────────────────────
    resultats_eto = models.JSONField(null=True, blank=True)
    resultats_cultures = models.JSONField(null=True, blank=True)
    resultats_crue = models.JSONField(null=True, blank=True)
    resultats_bilan_normale = models.JSONField(null=True, blank=True)
    resultats_bilan_humide = models.JSONField(null=True, blank=True)
    resultats_bilan_seche = models.JSONField(null=True, blank=True)

    date_calcul = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bilan Besoin-Ressources"
        verbose_name_plural = "Bilans Besoin-Ressources"
        ordering = ['-created_at']

    def __str__(self):
        date = self.created_at.strftime('%d/%m/%Y') if self.created_at else '—'
        return f"Bilan — {self.perimetre} ({date})"

    est_valide = models.BooleanField(default=False, verbose_name="Bilan validé")

    @property
    def est_calcule(self):
        return self.resultats_bilan_normale is not None


class BilanOuvrageAssocie(models.Model):
    """Ouvrage associé à un bilan — représente une ressource en eau.

    Un bilan peut associer plusieurs seuils/prises/khettaras/forages/barrages.
    Pour les seuils et prises locales, on capture aussi le BV, le Tc et le
    tronçon d'amenée choisi (avec son débit) au moment de la création.
    """

    TYPE_CHOICES = [
        ('seuil',        'Seuil'),
        ('prise_locale', 'Prise locale'),
        ('barrage',      'Barrage collinaire'),
        ('khettara',     'Khettara'),
        ('forage',       'Forage / Puits'),
    ]

    bilan = models.ForeignKey(
        BilanBesoinRessources,
        on_delete=models.CASCADE,
        related_name='ouvrages_associes',
        verbose_name="Bilan",
    )
    type_ouvrage = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Une seule des FK doit être non nulle selon `type_ouvrage`
    seuil = models.ForeignKey(
        'diagnostic.Seuil', on_delete=models.CASCADE,
        null=True, blank=True, related_name='bilans_associes',
    )
    prise_locale = models.ForeignKey(
        'diagnostic.PriseLocale', on_delete=models.CASCADE,
        null=True, blank=True, related_name='bilans_associes',
    )
    barrage = models.ForeignKey(
        'diagnostic.BarrageRetenue', on_delete=models.CASCADE,
        null=True, blank=True, related_name='bilans_associes',
    )
    khettara = models.ForeignKey(
        'diagnostic.Khettara', on_delete=models.CASCADE,
        null=True, blank=True, related_name='bilans_associes',
    )
    forage = models.ForeignKey(
        'diagnostic.ForagePuits', on_delete=models.CASCADE,
        null=True, blank=True, related_name='bilans_associes',
    )

    # Snapshot auto-rempli depuis l'ouvrage (seuil/prise) au moment du choix
    # Un seuil peut avoir 1 ou 2 tronçons d'amenée ; une prise locale en a 1
    # (seul troncon_amenee est utilisé, troncon_amenee_2 reste null).
    troncon_amenee = models.ForeignKey(
        'diagnostic.TronconSeguia', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bilans_ouvrages',
        verbose_name="Tronçon d'amenée",
    )
    troncon_amenee_2 = models.ForeignKey(
        'diagnostic.TronconSeguia', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bilans_ouvrages_secondaire',
        verbose_name="Tronçon d'amenée (2)",
        help_text="2e tronçon d'amenée (seuil uniquement, optionnel)",
    )
    bassin_versant = models.ForeignKey(
        'analyse_hydrologique.BassinVersant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='bilans_ouvrages',
    )
    tc_h = models.FloatField(null=True, blank=True, verbose_name="Tc (h)")
    tc_source = models.CharField(
        max_length=20, blank=True,
        help_text="'analyse' ou 'moyenne'",
    )
    debit_troncon_m3s = models.FloatField(null=True, blank=True, verbose_name="Débit tronçon (m³/s)")
    debit_troncon_2_m3s = models.FloatField(
        null=True, blank=True,
        verbose_name="Débit tronçon 2 (m³/s)",
        help_text="Débit du 2e tronçon d'amenée (seuil uniquement)",
    )

    # ── Paramètres saisis dans le bilan (selon le type d'ouvrage) ──────────────
    # Communs à tous les types (auto-rempli depuis l'ouvrage diagnostic) :
    efficience_reseau = models.FloatField(
        null=True, blank=True,
        verbose_name="Efficience du réseau (0–1)",
        help_text="Auto-rempli depuis l'ouvrage (défaut 0.75)",
    )

    # Seuil & Prise locale ──────────────────────────────────────────────────────
    # NB: nommé "amont" pour la cohérence scientifique (correction terminologique
    # suite à un retour utilisateur — la formule reste inchangée).
    debit_amont_m3s = models.FloatField(
        default=0.0, null=True, blank=True,
        verbose_name="Débit prélevé en amont (m³/s)",
        help_text="Volume prélevé dans d'autres périmètres en amont (défaut 0)",
    )
    # Prise locale uniquement
    capacite_deversement_pct = models.FloatField(
        default=100.0, null=True, blank=True,
        verbose_name="Capacité de déversement (%)",
        help_text="Dépend de l'angle de dérivation et de l'emplacement (défaut 100 %)",
    )

    # Khettara & Forage/Puits ───────────────────────────────────────────────────
    # L'utilisateur choisit : calcul avec khettarat ou transfert (mutuellement
    # exclusifs côté usage — les deux champs restent stockables).
    debit_khettarat_m3s = models.FloatField(
        null=True, blank=True,
        verbose_name="Débit khettara (m³/s)",
    )
    transfert_amont = models.BooleanField(
        default=False,
        verbose_name="Transfert amont activé",
    )
    debit_transfert_m3s = models.FloatField(
        null=True, blank=True,
        verbose_name="Débit de transfert (m³/s)",
    )
    tour_eau_jours = models.FloatField(
        default=1.0, null=True, blank=True,
        verbose_name="Tour d'eau (jours)",
    )
    duree_jours = models.FloatField(
        default=30.5, null=True, blank=True,
        verbose_name="Durée (jours)",
    )
    coeff_humide = models.FloatField(
        default=1.30, null=True, blank=True,
        verbose_name="Coefficient d'humidité",
    )
    coeff_seche = models.FloatField(
        default=0.80, null=True, blank=True,
        verbose_name="Coefficient de sécheresse",
    )

    # Barrage ───────────────────────────────────────────────────────────────────
    # Apports mensuels (m³, Sep→Aoû, 12 valeurs) pour 3 années — saisis par
    # l'utilisateur. L'efficience est appliquée au moment du calcul.
    apports_mensuels_normale = models.JSONField(
        null=True, blank=True,
        verbose_name="Apports mensuels année normale (m³, Sep→Aoû)",
    )
    apports_mensuels_humide = models.JSONField(
        null=True, blank=True,
        verbose_name="Apports mensuels année humide (m³, Sep→Aoû)",
    )
    apports_mensuels_seche = models.JSONField(
        null=True, blank=True,
        verbose_name="Apports mensuels année sèche (m³, Sep→Aoû)",
    )

    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Ouvrage associé au bilan"
        verbose_name_plural = "Ouvrages associés au bilan"

    def __str__(self):
        return f"{self.get_type_ouvrage_display()} — bilan {self.bilan_id}"

    @property
    def ouvrage(self):
        """Renvoie l'instance d'ouvrage selon `type_ouvrage`."""
        return {
            'seuil':        self.seuil,
            'prise_locale': self.prise_locale,
            'barrage':      self.barrage,
            'khettara':     self.khettara,
            'forage':       self.forage,
        }.get(self.type_ouvrage)


class AutreRessource(models.Model):
    """Ressource en eau indépendante du périmètre (parallèle aux ouvrages associés).

    Structure identique à un barrage : trois séries d'apports mensuels
    (normale / humide / sèche, 12 valeurs Sep→Aoû) et une efficience.
    """

    bilan = models.ForeignKey(
        BilanBesoinRessources,
        on_delete=models.CASCADE,
        related_name='autres_ressources_eau',
        verbose_name="Bilan",
    )
    nom = models.CharField(max_length=150, verbose_name="Nom de la ressource")

    apports_mensuels_normale = models.JSONField(
        null=True, blank=True,
        verbose_name="Apports mensuels année normale (m³, Sep→Aoû)",
    )
    apports_mensuels_humide = models.JSONField(
        null=True, blank=True,
        verbose_name="Apports mensuels année humide (m³, Sep→Aoû)",
    )
    apports_mensuels_seche = models.JSONField(
        null=True, blank=True,
        verbose_name="Apports mensuels année sèche (m³, Sep→Aoû)",
    )
    efficience = models.FloatField(
        default=0.80,
        verbose_name="Efficience (0–1)",
        help_text="Défaut 0.80 (80 %)",
    )

    ordre = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Autre ressource"
        verbose_name_plural = "Autres ressources"

    def __str__(self):
        return f"{self.nom} — bilan {self.bilan_id}"
