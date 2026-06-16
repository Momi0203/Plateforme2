from django.conf import settings
from django.db import models
from django.contrib.gis.db import models as gismodels
from django.utils import timezone


ETAT_CONSTRUCTION_CHOICES = [
    ('neuf', 'Neuf'),
    ('bon', 'Bon'),
    ('moyen', 'Moyen'),
    ('mauvais', 'Mauvais'),
    ('detruit', 'Détruit'),
]

STATUT_CHOICES = [
    ('non_valide', 'Non valide'),
    ('valide', 'Validé'),
]

# Échelle d'état utilisée pour le diagnostic structuré du seuil
ETAT_CONSTRUCTION_DIAG_CHOICES = [
    ('t_mauvais',     'Très mauvais'),
    ('mauvais',       'Mauvais'),
    ('moyen_mauvais', 'Moyen-mauvais'),
    ('moyen',         'Moyen'),
    ('moyen_bon',     'Moyen-bon'),
    ('bon',           'Bon'),
    ('excellent',     'Excellent'),
]

ETAT_MATERIEL_HYDROMECA_CHOICES = [
    ('absence',       'Absence'),
    ('t_mauvais',     'Très mauvais'),
    ('mauvais',       'Mauvais'),
    ('moyen_mauvais', 'Moyen-mauvais'),
    ('moyen',         'Moyen'),
    ('moyen_bon',     'Moyen-bon'),
    ('bon',           'Bon'),
    ('excellent',     'Excellent'),
]

# Notation 0-5 des critères détaillés du diagnostic d'un seuil
NOTE_CHOICES = [
    (0, 'Absence / aucun problème'),
    (1, 'Très faible'),
    (2, 'Faible'),
    (3, 'Moyen'),
    (4, 'Dégradé'),
    (5, 'Grave / critique'),
]

# Notation 0-5 dédiée au diagnostic des séguias (libellés différents)
NOTE_SEGUIA_CHOICES = [
    (0, 'Absence de désordre / état normal'),
    (1, 'Très bon état'),
    (2, 'Dégradation légère'),
    (3, 'Dégradation modérée'),
    (4, 'Dégradation importante'),
    (5, 'État critique / risque élevé'),
]

# Tronçons d'une séguia : TR1 → TR20
TRONCON_CHOICES = [(f'TR{i}', f'TR{i}') for i in range(1, 21)]

# Cultures du Tafilalet : référentiel commun aux modèles et formulaires
CULTURES_TAFILALET = [
    ("Abricot", "Abricot"), ("Agrumes", "Agrumes"), ("Amande", "Amande"),
    ("Betterave", "Betterave"), ("Blé", "Blé"), ("Carotte", "Carotte"),
    ("Citron", "Citron"), ("Clémentine", "Clémentine"), ("Cumin", "Cumin"),
    ("Datte", "Datte"), ("Figue", "Figue"), ("Grenade", "Grenade"),
    ("Luzerne", "Luzerne"), ("Mais", "Maïs"), ("Mandarine", "Mandarine"), ("Menthe", "Menthe"),
    ("Mûre", "Mûre"), ("Noix", "Noix"), ("Oignon", "Oignon"),
    ("Olive", "Olive"), ("Orange", "Orange"), ("Orge", "Orge"),
    ("Pastèque", "Pastèque"),("Peche", "Peche"), ("Piment", "Piment"), ("Pois", "Pois"),
    ("Pomme", "Pomme"), ("PommeTerre", "Pomme de terre"), ("Raisin", "Raisin"),
    ("Rose", "Rose"), ("Safran", "Safran"), ("Tomate", "Tomate"),
]


class DiagnosticSuiviMixin(models.Model):
    date_diagnostic = models.DateField(default=timezone.localdate)
    defaut_ouvrage = models.TextField(blank=True, default='', help_text="Texte libre sur les défauts observés")
    saisi_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_saisis',
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_valides',
    )

    class Meta:
        abstract = True


class Perimetre(models.Model):
    """Périmètre agricole"""

    province = models.CharField(max_length=100, default="Midelt")
    coordination = models.CharField(max_length=100, default="Midelt")
    commune_territoriale = models.CharField(max_length=100, blank=True)
    commune = models.ForeignKey(
        'carte.Commune',
        on_delete=models.SET_NULL,
        to_field='nom_fr',
        null=True, blank=True,
        related_name='perimetres',
        verbose_name="Commune (entité)",
    )
    ksar_village = models.CharField(max_length=100, blank=True)

    temperature_moyenne_annuelle = models.FloatField(null=True, blank=True)
    precipitations_moyennes_annuelles = models.FloatField(null=True, blank=True)
    vent = models.CharField(max_length=100, null=True, blank=True)
    humidite = models.CharField(max_length=100, null=True, blank=True)

    nombre_beneficiaires = models.PositiveIntegerField()
    nombre_menages = models.PositiveIntegerField()
    superficie_totale = models.FloatField()
    superficie_agricole_utile = models.FloatField()
    superficie_irriguee = models.FloatField()
    superficie_en_bour = models.FloatField(default=0)

    TYPE_SOL_CHOICES = [
        ('argileux', 'Argileux'),
        ('sableux', 'Sableux'),
        ('limoneux', 'Limoneux'),
        ('caillouteux', 'Caillouteux'),
        ('mixte', 'Mixte'),
    ]
    type_de_sol = models.CharField(max_length=50, default='argileux', choices=TYPE_SOL_CHOICES)

    NIVEAU_FERTILITE_CHOICES = [
        ('bon', 'Bon'),
        ('moyen', 'Moyen'),
        ('faible', 'Faible'),
    ]
    niveau_de_fertilite = models.CharField(max_length=50, default='bon', choices=NIVEAU_FERTILITE_CHOICES)

    parcelles_moins_1ha = models.FloatField(help_text="Pourcentage")
    parcelles_1_a_3ha = models.FloatField(help_text="Pourcentage")
    parcelles_plus_3ha = models.FloatField(help_text="Pourcentage")

    # ── Statut juridique des terres : 5 catégories fixes (taille fixe → colonnes,
    # pas de table enfant). Les listes JSON séparées ont été supprimées.
    statut_juridique_melk      = models.FloatField(null=True, blank=True, help_text="% melk")
    statut_juridique_collectif = models.FloatField(null=True, blank=True, help_text="% collectif")
    statut_juridique_location  = models.FloatField(null=True, blank=True, help_text="% location")
    statut_juridique_guiche    = models.FloatField(null=True, blank=True, help_text="% guich")
    statut_juridique_habousse  = models.FloatField(null=True, blank=True, help_text="% habous")

    # NB : les anciens JSONField cultures/pourcentage/rendement, ayants_droit_eau,
    # cycle_tour_eau_jours, duree_tour_eau_heures, organisations_agriculteurs,
    # ouvrages_en_tete_associes ont été remplacés par des tables enfants
    # (Assolement, TourEau, OrganisationAgriculteur, OuvrageTeteAssocie).

    moyenne_bovins = models.FloatField(null=True, blank=True, help_text="Moyenne du nombre de têtes/agriculteur (bovins)")
    moyenne_ovins = models.FloatField(null=True, blank=True, help_text="Moyenne du nombre de têtes/agriculteur (ovins)")
    moyenne_caprins = models.FloatField(null=True, blank=True, help_text="Moyenne du nombre de têtes/agriculteur (caprins)")

    efficiance_reseau = models.FloatField(
        default=0.9,
        verbose_name="Efficiance du réseau d'irrigation",
        help_text="Valeur entre 0 et 1 (défaut 0.9)",
    )

    et0_mm_jour = models.FloatField(
        null=True, blank=True,
        verbose_name="ET0 (mm/jour)",
        help_text="Évapotranspiration de référence en mm par jour — utilisée par le module efficiences",
    )

    volume_annee_normale = models.FloatField(
        null=True, blank=True,
        verbose_name="Volume — Année normale (m³)",
    )
    volume_annee_humide = models.FloatField(
        null=True, blank=True,
        verbose_name="Volume — Année humide (m³)",
    )
    volume_annee_seche = models.FloatField(
        null=True, blank=True,
        verbose_name="Volume — Année sèche (m³)",
    )
    volume_excedent_deficit_normale = models.FloatField(
        null=True, blank=True,
        verbose_name="Excédent/Déficit — Année normale (m³)",
    )
    volume_excedent_deficit_humide = models.FloatField(
        null=True, blank=True,
        verbose_name="Excédent/Déficit — Année humide (m³)",
    )
    volume_excedent_deficit_seche = models.FloatField(
        null=True, blank=True,
        verbose_name="Excédent/Déficit — Année sèche (m³)",
    )

    geometrie = gismodels.GeometryField(
        null=True, blank=True, srid=4326,
        verbose_name="Géométrie (polygone du périmètre)",
    )

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Périmètres"

    def __str__(self):
        return f"{self.ksar_village} - {self.commune_territoriale}"

    @property
    def cultures_bilan(self):
        """Compat templates : Kc_Kr_culture (référentiel global) dont le nom
        figure dans l'assolement de ce périmètre."""
        from Besions_Ressources.models import Kc_Kr_culture
        noms = self.assolement.values_list('culture', flat=True)
        return Kc_Kr_culture.objects.filter(nom__in=list(noms))


# ── Tables enfants liées à Périmètre (remplacent les anciens JSONField CSV) ──

class Assolement(models.Model):
    """Une ligne du tableau d'assolement d'un périmètre (culture pratiquée)."""

    UNITE_RENDEMENT_CHOICES = [
        ('qx_ha',    'qx/ha'),
        ('kg_arbre', 'kg/arbre'),
    ]

    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='assolement')
    culture = models.CharField(max_length=100, choices=CULTURES_TAFILALET)
    pourcentage = models.FloatField(null=True, blank=True, help_text="% de la surface cultivée")
    surface_ha = models.FloatField(null=True, blank=True, help_text="Surface (ha)")
    rendement = models.FloatField(null=True, blank=True, help_text="Rendement")
    unite_rendement = models.CharField(
        max_length=20, choices=UNITE_RENDEMENT_CHOICES, default='qx_ha',
        help_text="Unité du rendement",
    )
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Assolement"
        verbose_name_plural = "Assolements"

    def __str__(self):
        return f"{self.culture} — {self.perimetre}"


class TourEau(models.Model):
    """Tour d'eau pour un ayant droit du périmètre."""
    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='tours_eau')
    ayant_droit = models.CharField(max_length=200, help_text="Famille / ayant droit")
    cycle_jours = models.FloatField(null=True, blank=True)
    duree_heures = models.FloatField(null=True, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Tour d'eau"
        verbose_name_plural = "Tours d'eau"

    def __str__(self):
        return f"{self.ayant_droit} — {self.perimetre}"


class OrganisationAgriculteur(models.Model):
    """Organisation des agriculteurs d'un périmètre."""
    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='organisations')
    nom = models.CharField(max_length=200)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Organisation d'agriculteurs"
        verbose_name_plural = "Organisations d'agriculteurs"

    def __str__(self):
        return self.nom


class Seuil(DiagnosticSuiviMixin, models.Model):
    """Seuil hydraulique"""

    nom_du_seuil = models.CharField(max_length=100, unique=True)
    localisation_du_seuil = models.CharField(max_length=200, blank=True)
    coordonnes_x = models.FloatField(null=True, blank=True, help_text="Coordonnée X (Nord Maroc, m)")
    coordonnes_y = models.FloatField(null=True, blank=True, help_text="Coordonnée Y (Nord Maroc, m)")
    geometrie = gismodels.PointField(null=True, blank=True)

    nature_du_seuil = models.CharField(max_length=100)
    type_du_seuil = models.CharField(max_length=100)
    materiaux_de_construction = models.CharField(max_length=200)

    debit_mobilise = models.FloatField(help_text="l/s")
    longueur = models.FloatField()
    largeur_de_base = models.FloatField()
    hauteur = models.FloatField()
    largeur_tapis_amortissement = models.FloatField()

    longueur_prise_droit = models.FloatField(null=True, blank=True, help_text="Prise d'eau rive droite - Longueur")
    largeur_prise_droit = models.FloatField(null=True, blank=True, help_text="Prise d'eau rive droite - Largeur")
    nbr_pertuis_prise_droit = models.FloatField(null=True, blank=True, help_text="Prise d'eau rive droite - Nombre de pertuis")

    longueur_prise_gauche = models.FloatField(null=True, blank=True, help_text="Prise d'eau rive gauche - Longueur")
    largeur_prise_gauche = models.FloatField(null=True, blank=True, help_text="Prise d'eau rive gauche - Largeur")
    nbr_pertuis_prise_gauche = models.FloatField(null=True, blank=True, help_text="Prise d'eau rive gauche - Nombre de pertuis")

    longueur_degrevement_droit = models.FloatField(null=True, blank=True, help_text="Passe de dégrèvement rive droite - Longueur")
    largeur_degrevement_droit = models.FloatField(null=True, blank=True, help_text="Passe de dégrèvement rive droite - Largeur")
    nbr_pertuis_degrevement_droit = models.FloatField(null=True, blank=True, help_text="Passe de dégrèvement rive droite - Nombre de pertuis")

    longueur_degrevement_gauche = models.FloatField(null=True, blank=True, help_text="Passe de dégrèvement rive gauche - Longueur")
    largeur_degrevement_gauche = models.FloatField(null=True, blank=True, help_text="Passe de dégrèvement rive gauche - Largeur")
    nbr_pertuis_degrevement_gauche = models.FloatField(null=True, blank=True, help_text="Passe de dégrèvement rive gauche - Nombre de pertuis")

    etat_construction_fonctionnement = models.TextField(blank=True, help_text="Texte libre (legacy — voir EtatSeuil)")
    etat_materiel_hydromecanique = models.CharField(max_length=500, blank=True, help_text="Texte legacy — voir EtatSeuil")

    annee_derniere_rehabilitation = models.IntegerField(null=True, blank=True)

    efficience_reseaux = models.FloatField(default=0.75, null=True, blank=True, help_text="Efficience du réseau (0–1, défaut 0.75)")
    bassin_versant = models.ForeignKey(
        'analyse_hydrologique.BassinVersant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='seuils',
    )

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='seuils')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Seuils"

    def __str__(self):
        return self.nom_du_seuil


class EtatSeuil(models.Model):
    """Diagnostic structuré de l'état d'un seuil (état général + 10 critères notés)."""

    seuil = models.OneToOneField(
        Seuil,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='diagnostic_etat',
    )
    date_diagnostic = models.DateField(default=timezone.localdate)

    etat_construction_fonctionnement = models.CharField(
        max_length=20, choices=ETAT_CONSTRUCTION_DIAG_CHOICES, blank=True,
        verbose_name="État construction / fonctionnement",
    )
    etat_materiel_hydromecanique = models.CharField(
        max_length=20, choices=ETAT_MATERIEL_HYDROMECA_CHOICES, blank=True,
        verbose_name="État matériel hydromécanique",
    )

    etat_structurel_digue = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="État structurel de la digue")
    affouillement_aval = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="Affouillement à l'aval")
    envasement_retenue = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="Envasement de la retenue")
    murs_guideaux = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="Murs guideaux")
    radier_aval = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="Radier aval")
    etat_vannes = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="État des vannes")
    dessableur = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="Dessableur")
    degradation_beton = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="Dégradation du béton")
    infiltration_fuite = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="Infiltration / fuite")
    limiteur_debit = models.IntegerField(choices=NOTE_CHOICES, null=True, blank=True, verbose_name="Limiteur de débit")

    editeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etat_seuils_edites',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "État de seuil (diagnostic)"
        verbose_name_plural = "États des seuils (diagnostics)"

    def __str__(self):
        return f"État — {self.seuil.nom_du_seuil}"


class MurProtection(DiagnosticSuiviMixin, models.Model):
    """Mur de protection"""

    nom_mur_protection = models.CharField(max_length=100, unique=True, null=True, blank=True)

    RIVE_CHOICES = [
        ('droite', 'Rive droite'),
        ('gauche', 'Rive gauche'),
    ]
    rive = models.CharField(max_length=20, choices=RIVE_CHOICES)

    POSITION_CHOICES = [
        ('amont', 'Amont'),
        ('aval', 'Aval'),
    ]
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)

    nature_materiaux = models.CharField(max_length=100)
    longueur = models.FloatField()
    hauteur = models.FloatField()
    epaisseur_superieure = models.FloatField()
    epaisseur_inferieure = models.FloatField()

    etat_construction = models.TextField(blank=True, help_text="Texte libre (legacy — voir EtatMurProtection)")

    efficience_reseaux = models.FloatField(default=0.75, null=True, blank=True, help_text="Efficience du réseau (0–1, défaut 0.75)")

    ouvrage_associe = models.ForeignKey(Seuil, on_delete=models.CASCADE, related_name='murs_protection', null=True, blank=True)
    geometrie = gismodels.PointField(null=True, blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='murs_protection')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Murs de protection"

    def __str__(self):
        return self.nom_mur_protection or f"Mur {self.rive} - {self.position}"


class EtatMurProtection(models.Model):
    """Diagnostic structuré de l'état d'un mur de protection (état général + 3 critères notés)."""

    mur = models.OneToOneField(
        MurProtection,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='diagnostic_etat',
    )
    date_diagnostic = models.DateField(default=timezone.localdate)

    etat_general = models.CharField(
        max_length=20, choices=ETAT_CONSTRUCTION_DIAG_CHOICES, blank=True,
        verbose_name="État général",
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")

    fissures_revetement   = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Fissures du revêtement")
    degradation_beton     = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Dégradation du béton")
    risque_contournement  = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Risque de contournement")

    editeur_operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etat_murs_edites',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "État de mur (diagnostic)"
        verbose_name_plural = "États des murs (diagnostics)"

    def __str__(self):
        return f"État — {self.mur}"


class Seguias(DiagnosticSuiviMixin, models.Model):
    """Séguia (canal d'irrigation) — identité uniquement.
    Les tronçons (dimensions, efficiences, géométrie) sont dans TronconSeguia."""

    nom_de_la_seguia = models.CharField(max_length=100)

    TYPE_SEGUIA_CHOICES = [
        ('principale', 'Principale'),
        ('secondaire', 'Secondaire'),
        ('tertiaire', 'Tertiaire'),
    ]
    type_deguia = models.CharField(max_length=20, choices=TYPE_SEGUIA_CHOICES)

    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='seguias')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Séguias"

    def __str__(self):
        return self.nom_de_la_seguia


FORME_SEGUIA_CHOICES = [
    ('trapezoidale',  'Trapézoïdale'),
    ('rectangulaire', 'Rectangulaire'),
    ('circulaire',    'Circulaire'),
]

NATURE_SEGUIA_CHOICES = [
    ('beton',      'Béton'),
    ('beton_arme', 'Béton armé'),
    ('terre',      'Terre'),
    ('autre',      'Autre'),
]

TYPE_ECOULEMENT_CHOICES = [
    ('dalot',      'Dalot'),
    ('ciel_ouvert', 'À ciel ouvert'),
]


class TronconSeguia(models.Model):
    """Tronçon d'une séguia : dimensions, efficiences et géométrie.
    Une séguia peut contenir plusieurs tronçons (TR1–TR20)."""

    seguia = models.ForeignKey(
        Seguias,
        on_delete=models.CASCADE,
        related_name='troncons',
        verbose_name="Séguia parente",
    )
    troncon = models.CharField(max_length=10, choices=TRONCON_CHOICES, verbose_name="Tronçon")

    forme = models.CharField(
        max_length=20, choices=FORME_SEGUIA_CHOICES, default='trapezoidale',
        verbose_name="Forme",
    )
    longueur = models.FloatField(verbose_name="Longueur (m)")
    largeur_meroire = models.FloatField(null=True, blank=True, verbose_name="Largeur miroir (m)")
    hauteur = models.FloatField(null=True, blank=True, verbose_name="Hauteur (m)")
    hauteur_eau = models.FloatField(verbose_name="Hauteur d'eau (m)")
    fruit_de_berge = models.FloatField(null=True, blank=True, default=0, verbose_name="Fruit de berge")
    epaisseur_parois = models.FloatField(verbose_name="Épaisseur parois (m)")
    diametre = models.FloatField(
        null=True, blank=True,
        verbose_name="Diamètre (m)",
        help_text="Requis pour la forme circulaire",
    )
    nature = models.CharField(max_length=20, choices=NATURE_SEGUIA_CHOICES, verbose_name="Nature")
    debit = models.FloatField(verbose_name="Débit (m³/s)")
    type_decoulement = models.CharField(
        max_length=20, choices=TYPE_ECOULEMENT_CHOICES, verbose_name="Type d'écoulement",
    )

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')

    efficience_trancons = models.FloatField(
        default=0.75, null=True, blank=True,
        verbose_name="Efficience saisie (0–1)",
    )
    efficience_calculee = models.FloatField(
        null=True, blank=True, verbose_name="Efficience calculée (%)",
    )
    perte_infiltration_m3s = models.FloatField(
        null=True, blank=True, verbose_name="Perte infiltration (m³/s)",
    )
    perte_vaporisation_m3s = models.FloatField(
        null=True, blank=True, verbose_name="Perte évaporation (m³/s)",
    )
    date_dernier_calcul = models.DateTimeField(
        null=True, blank=True, verbose_name="Date dernier calcul",
    )

    geometrie = gismodels.LineStringField(null=True, blank=True, verbose_name="Géométrie")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tronçon de séguia"
        verbose_name_plural = "Tronçons de séguias"
        unique_together = [('seguia', 'troncon')]
        ordering = ['seguia', 'troncon']

    def __str__(self):
        return f"{self.seguia.nom_de_la_seguia} — {self.troncon}"


class EtatTronconSeguia(models.Model):
    """Diagnostic structuré de l'état d'un tronçon de séguia (état général + 7 critères notés)."""

    troncon = models.OneToOneField(
        TronconSeguia,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='diagnostic_etat',
    )
    date_diagnostic = models.DateField(default=timezone.localdate)

    etat_general = models.CharField(
        max_length=20, choices=ETAT_CONSTRUCTION_DIAG_CHOICES, blank=True,
        verbose_name="État général",
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")

    fissures_revetement = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Fissures du revêtement")
    infiltration_fuite  = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Infiltration / fuite")
    obstructions_debris = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Obstructions / débris")
    erosion_berges      = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Érosion des berges")
    sedimentation_fond  = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Sédimentation au fond")
    ouvrages_regulation = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Ouvrages de régulation")
    spalling_beton      = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Spalling du béton")

    editeur_operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etat_troncons_seguia_edites',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "État de tronçon de séguia (diagnostic)"
        verbose_name_plural = "États des tronçons de séguias (diagnostics)"

    def __str__(self):
        return f"État — {self.troncon}"


class BarrageRetenue(DiagnosticSuiviMixin, models.Model):
    """Barrage de retenue et lac collinaire"""

    nom = models.CharField(max_length=100, unique=True)

    coordonnees_lambert_x = models.FloatField()
    coordonnees_lambert_y = models.FloatField()

    debit_derive = models.FloatField()
    volume_attribue_irrigation = models.FloatField()
    capacite_retenue = models.FloatField()

    longueur = models.FloatField()
    largeur = models.FloatField()
    hauteur = models.FloatField()

    materiaux_de_construction = models.CharField(max_length=200)

    etat_construction_fonctionnement = models.TextField(blank=True, help_text="Texte libre (legacy — voir EtatBarrageRetenue)")

    efficience_reseaux = models.FloatField(default=0.75, null=True, blank=True, help_text="Efficience du réseau (0–1, défaut 0.75)")
    bassin_versant = models.ForeignKey(
        'analyse_hydrologique.BassinVersant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='barrages_retenue',
    )

    geometrie = gismodels.PointField(null=True, blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='barrages_retenue')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Barrages de retenue et lacs collinaires"

    def __str__(self):
        return self.nom


class EtatBarrageRetenue(models.Model):
    """Diagnostic structuré de l'état d'un barrage de retenue (état général + 4 critères notés)."""

    barrage = models.OneToOneField(
        BarrageRetenue,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='diagnostic_etat',
    )
    date_diagnostic = models.DateField(default=timezone.localdate)

    etat_general = models.CharField(
        max_length=20, choices=ETAT_CONSTRUCTION_DIAG_CHOICES, blank=True,
        verbose_name="État général",
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")

    affouillement_pied_digue_aval     = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Affouillement au pied de digue aval")
    taux_envasement_retenue           = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Taux d'envasement de la retenue")
    regulation_debits_aval            = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Régulation des débits aval")
    fonctionnement_ouvrages_prise_eau = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Fonctionnement des ouvrages de prise d'eau")

    editeur_operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etat_barrages_edites',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "État de barrage (diagnostic)"
        verbose_name_plural = "États des barrages (diagnostics)"

    def __str__(self):
        return f"État — {self.barrage.nom}"


class Khettara(DiagnosticSuiviMixin, models.Model):
    """Khettara (système d'irrigation traditionnel)"""

    nom = models.CharField(max_length=100, unique=True)

    coordonnees_lambert_x = models.FloatField()
    coordonnees_lambert_y = models.FloatField()

    debit = models.FloatField()
    longueur = models.FloatField()
    largeur = models.FloatField()
    hauteur = models.FloatField()

    materiaux_de_construction = models.CharField(max_length=200)

    etat_construction_fonctionnement = models.TextField(blank=True, help_text="Texte libre (legacy — voir EtatKhettara)")

    efficience_reseaux = models.FloatField(default=0.75, null=True, blank=True, help_text="Efficience du réseau (0–1, défaut 0.75)")

    geometrie = gismodels.PointField(null=True, blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='khettaras')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Khettaras"

    def __str__(self):
        return self.nom


class EtatKhettara(models.Model):
    """Diagnostic structuré de l'état d'une khettara (état général + 4 critères notés)."""

    khettara = models.OneToOneField(
        Khettara,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='diagnostic_etat',
    )
    date_diagnostic = models.DateField(default=timezone.localdate)

    etat_general = models.CharField(
        max_length=20, choices=ETAT_CONSTRUCTION_DIAG_CHOICES, blank=True,
        verbose_name="État général",
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")

    envasement_ensablement_fond  = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Envasement / ensablement du fond")
    degradation_beton            = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Dégradation du béton")
    accessibilite_entretien      = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Accessibilité pour l'entretien")
    stabilite_galerie_principale = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Stabilité de la galerie principale")

    editeur_operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etat_khettaras_edites',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "État de khettara (diagnostic)"
        verbose_name_plural = "États des khettaras (diagnostics)"

    def __str__(self):
        return f"État — {self.khettara.nom}"


class ForagePuits(DiagnosticSuiviMixin, models.Model):
    """Forage / Puits d'irrigation (Collectif)"""

    nom = models.CharField(max_length=100, unique=True)

    coordonnees_lambert_x = models.FloatField()
    coordonnees_lambert_y = models.FloatField()

    debit = models.FloatField(help_text="m³/h")
    profondeur = models.FloatField()
    diametre = models.FloatField()

    equipements_associes = models.CharField(max_length=200, blank=True)

    SOURCE_ENERGIE_CHOICES = [
        ('electricite_reseau', 'Électricité réseau'),
        ('energie_solaire',    'Énergie solaire'),
        ('electrogene_diesel', 'Électrogène diesel'),
        ('systemes_hybrides',  'Systèmes hybrides'),
        # ── Valeurs legacy (rétrocompat avec les enregistrements existants)
        ('electrique', 'Électrique (legacy)'),
        ('diesel',     'Diesel (legacy)'),
        ('solaire',    'Solaire (legacy)'),
        ('manuel',     'Manuel (legacy)'),
        ('autre',      'Autre (legacy)'),
    ]
    source_energie_pompage = models.CharField(max_length=20, choices=SOURCE_ENERGIE_CHOICES)

    etat_construction_fonctionnement = models.TextField(blank=True, help_text="Texte libre (legacy — voir EtatForagePuits)")

    efficience_reseaux = models.FloatField(default=0.75, null=True, blank=True, help_text="Efficience du réseau (0–1, défaut 0.75)")

    geometrie = gismodels.PointField(null=True, blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='forages_puits')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Forages / Puits d'irrigation (Collectif)"

    def __str__(self):
        return self.nom


class EtatForagePuits(models.Model):
    """Diagnostic structuré de l'état d'un forage/puits (état général + 4 critères notés)."""

    forage = models.OneToOneField(
        ForagePuits,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='diagnostic_etat',
    )
    date_diagnostic = models.DateField(default=timezone.localdate)

    etat_general = models.CharField(
        max_length=20, choices=ETAT_CONSTRUCTION_DIAG_CHOICES, blank=True,
        verbose_name="État général",
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")

    qualite_physico_chimique_eau   = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Qualité physico-chimique de l'eau")
    degradation_structurelle_forage = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Dégradation structurelle du forage")
    colmatage_forage                = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Colmatage du forage")
    etat_equipements                = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="État des équipements")

    editeur_operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etat_forages_edites',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "État de forage/puits (diagnostic)"
        verbose_name_plural = "États des forages/puits (diagnostics)"

    def __str__(self):
        return f"État — {self.forage.nom}"


class PriseLocale(DiagnosticSuiviMixin, models.Model):
    """Prise locale (ouvrage en tête)"""

    FORME_PERTUIS_CHOICES = [
        ('trapezoidale', 'Trapézoïdale'),
        ('rectangulaire', 'Rectangulaire'),
        ('circulaire', 'Circulaire'),
    ]

    nom = models.CharField(max_length=100, unique=True)
    coordonnee_x = models.FloatField(null=True, blank=True, help_text="Nord Maroc X (m)")
    coordonnee_y = models.FloatField(null=True, blank=True, help_text="Nord Maroc Y (m)")
    materiaux_construction = models.CharField(max_length=200, blank=True)

    forme_pertuis = models.CharField(max_length=20, choices=FORME_PERTUIS_CHOICES, blank=True)

    # Trapézoïdale et rectangulaire
    largeur_au_miroir = models.FloatField(null=True, blank=True, help_text="m")
    hauteur_pertuis = models.FloatField(null=True, blank=True, help_text="m")
    fruit_pente = models.FloatField(null=True, blank=True, help_text="m (fruit de la pente)")

    # Circulaire seulement
    diametre = models.FloatField(null=True, blank=True, help_text="m")

    debit_derive = models.FloatField(null=True, blank=True, help_text="m³/s")

    etat_fonctionnement = models.TextField(blank=True, help_text="Texte libre (legacy — voir EtatPriseLocale)")

    efficience_reseaux = models.FloatField(default=0.75, null=True, blank=True, help_text="Efficience du réseau (0–1, défaut 0.75)")
    bassin_versant = models.ForeignKey(
        'analyse_hydrologique.BassinVersant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prises_locales',
    )

    geometrie = gismodels.PointField(null=True, blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    perimetre = models.ForeignKey(Perimetre, on_delete=models.CASCADE, related_name='prises_locales')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Prises locales"

    def __str__(self):
        return self.nom


class EtatPriseLocale(models.Model):
    """Diagnostic structuré de l'état d'une prise locale (état général + 5 critères notés)."""

    prise = models.OneToOneField(
        PriseLocale,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='diagnostic_etat',
    )
    date_diagnostic = models.DateField(default=timezone.localdate)

    etat_general = models.CharField(
        max_length=20, choices=ETAT_CONSTRUCTION_DIAG_CHOICES, blank=True,
        verbose_name="État général",
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")

    envasement_sedimentation_entree = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Envasement / sédimentation à l'entrée")
    degradation_revetement          = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Dégradation du revêtement")
    accumulation_debris_vegetation  = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Accumulation de débris / végétation")
    etat_dispositifs_regulation     = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="État des dispositifs de régulation (vannes, masques)")
    protection_crues_debordements   = models.IntegerField(choices=NOTE_SEGUIA_CHOICES, null=True, blank=True, verbose_name="Protection contre crues / débordements")

    editeur_operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etat_prises_edites',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "État de prise locale (diagnostic)"
        verbose_name_plural = "États des prises locales (diagnostics)"

    def __str__(self):
        return f"État — {self.prise.nom}"


class SguiaAssocie_OuvrageTete(models.Model):
    """Liaison N–N entre une séguia et les ouvrages en tête associés.

    Une ligne représente l'association d'une séguia à un ou plusieurs ouvrages
    de tête de différents types (seuil, khettara, prise locale, forage/puits,
    barrage). Tous les FK sont optionnels — au moins un doit être renseigné.
    """

    FK_nom_sguia = models.ForeignKey(
        Seguias,
        on_delete=models.CASCADE,
        related_name='ouvrages_tete_associes',
        verbose_name="Séguia",
    )
    FK_seuil = models.ForeignKey(
        Seuil, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguias_associees',
    )
    FK_khettaras = models.ForeignKey(
        Khettara, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguias_associees',
    )
    FK_prise_locale = models.ForeignKey(
        PriseLocale, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguias_associees',
    )
    FK_puit_forage = models.ForeignKey(
        ForagePuits, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguias_associees',
    )
    FK_barrage_retenue = models.ForeignKey(
        BarrageRetenue, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguias_associees',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Séguia / Ouvrage de tête (association)"
        verbose_name_plural = "Séguias / Ouvrages de tête (associations)"

    def __str__(self):
        return f"{self.FK_nom_sguia} ↔ ouvrages de tête"
