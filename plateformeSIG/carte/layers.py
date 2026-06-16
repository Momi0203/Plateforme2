# Registre central des couches cartographiques.
# Source de vérité : cc-projet/02_perimetre_couches.md §4 — 15 couches.
# Ajouter une couche = une entrée ici. Aucune modification JS requise.

LAYER_REGISTRY = {

    # ── Groupe : Administratif ──────────────────────────────────────────────
    "provinces": {
        "model":      "carte.Province",
        "geom_field": "geometrie",
        "geom_type":  "Polygon",
        "groupe":     "Administratif",
        "label":      "Provinces",
        "fields": [
            "nom_fr", "nom_ar", "superficie_km2", "population_totale",
            "temp_moy_annuelle_c", "precip_annuelle_mm", "et0_annuelle_mm",
        ],
    },
    "communes": {
        "model":      "carte.Commune",
        "geom_field": "geometrie",
        "geom_type":  "Polygon",
        "groupe":     "Administratif",
        "label":      "Communes",
        "fields": [
            "nom_fr", "type_commune", "population_totale",
            "superficie_km2", "nbr_perimetres_agricoles",
            "province",   # FK → Province.pk (drill-down §5.1.6)
        ],
    },

    # ── Groupe : Hydrologie ─────────────────────────────────────────────────
    "bassins_versants": {
        "model":      "carte.BassinVersant",
        "geom_field": "geometrie",
        "geom_type":  "Polygon",
        "groupe":     "Hydrologie",
        "label":      "Bassins versants",
        "fields": [
            "nom", "superficie_km2", "perimetre_km",
            "altitude_min", "altitude_max", "altitude_exutoire",
            "thalweg_km",
            "precipitations_annuelles_mm", "evapotranspiration_annuelle_mm",
        ],
    },
    "reseau_hydrographique": {
        "model":      "carte.ReseauHydrographique",
        "geom_field": "geometrie",
        "geom_type":  "LineString",
        "groupe":     "Hydrologie",
        "label":      "Réseau hydrographique",
        "fields": ["bassin_versant", "comid", "sorder"],
    },
    "stations_pluvio": {
        "model":      "analyse_hydrologique.StationPluviometrique",
        "geom_field": "geom_point",
        "geom_type":  "Point",
        "groupe":     "Hydrologie",
        "label":      "Stations pluviométriques",
        "fields": [
            "nom", "hauteur_moyenne",
            "pjmax_t10", "pjmax_t20", "pjmax_t50", "pjmax_t100",
        ],
    },
    "stations_hydro": {
        "model":      "analyse_hydrologique.StationHydrometrique",
        "geom_field": "geometrie",
        "geom_type":  "Point",
        "groupe":     "Hydrologie",
        "label":      "Stations hydrométriques",
        "fields": [
            "nom", "superficie_bv_jaugee",
            "qjmax_t10", "qjmax_t20", "qjmax_t50", "qjmax_t100",
            "debits_mensuels_annee_humide",
            "debits_mensuels_annee_normale",
            "debits_mensuels_annee_seche",
        ],
    },
    "stations_clim": {
        "model":      "Besions_Ressources.StationClimatique",
        "geom_field": "geometrie",
        "geom_type":  "Point",
        "groupe":     "Hydrologie",
        "label":      "Stations climatiques",
        "fields": [
            "nom", "latitude",
            "temperatures_moyennes", "precipitations_normales",
        ],
    },
    # Bassins versants de l'app analyse_hydrologique (ceux qui portent les
    # analyses de crue / Tc / ouvrages de tête). MASQUÉE du panneau gauche
    # (`hidden`) : servie uniquement aux outils de la box « Hydrologie / Crues ».
    # NB : modèle distinct de carte.BassinVersant (couche "bassins_versants").
    "bv_ouvrage_tete": {
        "model":      "analyse_hydrologique.BassinVersant",
        "geom_field": "geometrie",
        "geom_type":  "Polygon",
        "groupe":     "Hydrologie",
        "label":      "Bassins versants (ouvrage de tête)",
        "fields": [
            "nom", "surface", "perimetre",
            "z_min", "z_max", "thalweg", "ouvrage_en_tete",
        ],
        "hidden": True,
        # Activable à la demande via la box « Couches » → groupe panneau gauche.
        "groupe_activable": "Réseaux ouvrage de tête",
    },

    # ── Réseaux hydrographiques « ouvrage de tête » par bassin ──────────────
    # MASQUÉS du panneau gauche + activables via la box « Couches ». Volumineux
    # (Ziz ~152k, Moulouya ~82k tronçons) : NE PAS charger en entier — affichés
    # uniquement clippés à un BV via l'outil « Réseau du BV »
    # (endpoint reseau_ouvrage_tete). `reseau_tete: True` → le panneau gauche
    # remplace le bouton multicritère par le bouton « Réseau du BV ».
    "reseau_tete_ziz": {
        "model":      "carte.ReseauOuvrageTeteZiz",
        "geom_field": "geometrie", "geom_type": "LineString",
        "groupe":     "Réseaux ouvrage de tête", "label": "Réseau ouvrage de tête — Ziz",
        "fields":     ["grid_code"],
        "hidden": True, "groupe_activable": "Réseaux ouvrage de tête", "reseau_tete": True,
    },
    "reseau_tete_moulouya": {
        "model":      "carte.ReseauOuvrageTeteMoulouya",
        "geom_field": "geometrie", "geom_type": "LineString",
        "groupe":     "Réseaux ouvrage de tête", "label": "Réseau ouvrage de tête — Moulouya",
        "fields":     ["grid_code"],
        "hidden": True, "groupe_activable": "Réseaux ouvrage de tête", "reseau_tete": True,
    },
    "reseau_tete_guir": {
        "model":      "carte.ReseauOuvrageTeteGuir",
        "geom_field": "geometrie", "geom_type": "LineString",
        "groupe":     "Réseaux ouvrage de tête", "label": "Réseau ouvrage de tête — Guir",
        "fields":     ["grid_code"],
        "hidden": True, "groupe_activable": "Réseaux ouvrage de tête", "reseau_tete": True,
    },
    "reseau_tete_rheris": {
        "model":      "carte.ReseauOuvrageTeteRheris",
        "geom_field": "geometrie", "geom_type": "LineString",
        "groupe":     "Réseaux ouvrage de tête", "label": "Réseau ouvrage de tête — Rhéris",
        "fields":     ["grid_code"],
        "hidden": True, "groupe_activable": "Réseaux ouvrage de tête", "reseau_tete": True,
    },
    "reseau_tete_maider": {
        "model":      "carte.ReseauOuvrageTeteMaider",
        "geom_field": "geometrie", "geom_type": "LineString",
        "groupe":     "Réseaux ouvrage de tête", "label": "Réseau ouvrage de tête — Maïder",
        "fields":     ["grid_code"],
        "hidden": True, "groupe_activable": "Réseaux ouvrage de tête", "reseau_tete": True,
    },

    # ── Groupe : Diagnostic ─────────────────────────────────────────────────
    "perimetres": {
        "model":      "diagnostic.Perimetre",
        "geom_field": "geometrie",
        "geom_type":  "Geometry",
        "groupe":     "Diagnostic",
        "label":      "Périmètres agricoles",
        "fields": [
            "ksar_village", "commune_territoriale",
            "superficie_totale", "superficie_irriguee",
            "nombre_beneficiaires", "statut",
        ],
    },
    "seuils": {
        "model":      "diagnostic.Seuil",
        "geom_field": "geometrie",
        "geom_type":  "Point",
        "groupe":     "Diagnostic",
        "label":      "Seuils",
        "fields": [
            "nom_du_seuil", "nature_du_seuil", "type_du_seuil",
            "debit_mobilise", "longueur", "hauteur", "statut",
            "bassin_versant",   # FK → BassinVersant.pk (drill-down §5.1.6)
        ],
        "join_etat":  "diagnostic_etat",
        "etat_lookup": "diagnostic_etat__etat_construction_fonctionnement",
        "scoring_champs": [
            "etat_structurel_digue", "affouillement_aval", "envasement_retenue",
            "murs_guideaux", "radier_aval", "etat_vannes", "dessableur",
            "degradation_beton", "infiltration_fuite", "limiteur_debit",
        ],
    },
    "murs_protection": {
        "model":      "diagnostic.MurProtection",
        "geom_field": "geometrie",
        "geom_type":  "Point",          # MurProtection.geometrie = PointField
        "groupe":     "Diagnostic",
        "label":      "Murs de protection",
        "fields": [
            "nom_mur_protection", "rive", "position",
            "nature_materiaux", "longueur", "statut",
        ],
        "join_etat":  "diagnostic_etat",
        "etat_lookup": "diagnostic_etat__etat_general",
        "scoring_champs": [
            "fissures_revetement", "degradation_beton", "risque_contournement",
        ],
    },
    "troncons_seguias": {
        "model":      "diagnostic.TronconSeguia",
        "geom_field": "geometrie",
        "geom_type":  "LineString",     # TronconSeguia.geometrie = LineStringField
        "groupe":     "Diagnostic",
        "label":      "Tronçons de séguias",
        "fields": [
            "troncon", "longueur", "nature", "debit",
            "efficience_calculee", "statut",
        ],
        "join_etat":  "diagnostic_etat",
        "etat_lookup": "diagnostic_etat__etat_general",
        "scoring_champs": [
            "fissures_revetement", "infiltration_fuite", "obstructions_debris",
            "erosion_berges", "sedimentation_fond", "ouvrages_regulation", "spalling_beton",
        ],
    },
    "barrages": {
        "model":      "diagnostic.BarrageRetenue",
        "geom_field": "geometrie",
        "geom_type":  "Point",          # BarrageRetenue.geometrie = PointField
        "groupe":     "Diagnostic",
        "label":      "Barrages de retenue",
        "fields": [
            "nom", "capacite_retenue", "debit_derive",
            "longueur", "hauteur", "statut",
            "bassin_versant",   # FK → BassinVersant.pk (drill-down §5.1.6)
        ],
        "join_etat":  "diagnostic_etat",
        "etat_lookup": "diagnostic_etat__etat_general",
        "scoring_champs": [
            "affouillement_pied_digue_aval", "taux_envasement_retenue",
            "regulation_debits_aval", "fonctionnement_ouvrages_prise_eau",
        ],
    },
    "khettaras": {
        "model":      "diagnostic.Khettara",
        "geom_field": "geometrie",
        "geom_type":  "Point",          # Khettara.geometrie = PointField
        "groupe":     "Diagnostic",
        "label":      "Khettaras",
        "fields": [
            "nom", "debit", "longueur", "largeur",
            "materiaux_de_construction", "statut",
        ],
        "join_etat":  "diagnostic_etat",
        "etat_lookup": "diagnostic_etat__etat_general",
        "scoring_champs": [
            "envasement_ensablement_fond", "degradation_beton",
            "accessibilite_entretien", "stabilite_galerie_principale",
        ],
    },
    "forages_puits": {
        "model":      "diagnostic.ForagePuits",
        "geom_field": "geometrie",
        "geom_type":  "Point",          # ForagePuits.geometrie = PointField
        "groupe":     "Diagnostic",
        "label":      "Forages / Puits",
        "fields": [
            "nom", "debit", "profondeur", "diametre",
            "source_energie_pompage", "statut",
        ],
        "join_etat":  "diagnostic_etat",
        "etat_lookup": "diagnostic_etat__etat_general",
        "scoring_champs": [
            "qualite_physico_chimique_eau", "degradation_structurelle_forage",
            "colmatage_forage", "etat_equipements",
        ],
    },
    "prises_locales": {
        "model":      "diagnostic.PriseLocale",
        "geom_field": "geometrie",
        "geom_type":  "Point",          # PriseLocale.geometrie = PointField
        "groupe":     "Diagnostic",
        "label":      "Prises locales",
        "fields": [
            "nom", "forme_pertuis", "debit_derive",
            "materiaux_construction", "statut",
            "bassin_versant",   # FK → BassinVersant.pk (drill-down §5.1.6)
        ],
        "join_etat":  "diagnostic_etat",
        "etat_lookup": "diagnostic_etat__etat_general",
        "scoring_champs": [
            "envasement_sedimentation_entree", "degradation_revetement",
            "accumulation_debris_vegetation", "etat_dispositifs_regulation",
            "protection_crues_debordements",
        ],
    },
}
