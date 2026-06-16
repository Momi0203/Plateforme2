---
section: "02"
titre: "Périmètre fonctionnel et inventaire des couches"
version: "2.0"
date: "2026-06-04"
tags: [fonctionnalités, couches, GeoJSON, PostGIS]
---

# §3 — Périmètre fonctionnel et §4 — Inventaire des couches

## 3.1 Fonctionnalités V1

| ID | Fonctionnalité | Priorité |
|---|---|---|
| F-01 | Affichage cartographique des couches PostGIS | MUST |
| F-02 | Gestionnaire de couches (arborescence, visibilité, ordre) | MUST |
| F-03 | Sélection d'entités (rectangle, polygone, clic) | MUST |
| F-04 | Requête attributaire simple (une condition) | MUST |
| F-05 | Requête multicritère avec opérateurs logiques AND/OR | MUST |
| F-06 | Symbologie simple (couleur, taille, opacité) | MUST |
| F-07 | Symbologie catégorisée et graduée | MUST |
| F-08 | Bibliothèque de styles personnels | SHOULD |
| F-09 | Outils d'analyse : tampon, intersection, proximité | MUST |
| F-10 | Outils de gestion : merge, dissolve, jointure spatiale | SHOULD |
| F-11 | Calculatrice de champ | SHOULD |
| F-12 | Requête SQL avancée avec fonctions spatiales PostGIS | COULD |
| F-13 | Vue carte avec export A4–A0 PDF/PNG | MUST |
| F-14 | Vue dashboard avec graphiques liés à la sélection | MUST |
| F-15 | Vue tableau attributaire avec tri/filtre/pagination | MUST |
| F-16 | Export tableau CSV / Excel / JSON | MUST |
| F-17 | Export dashboard PDF / PNG | SHOULD |
| F-18 | Synchronisation carte ↔ tableau ↔ dashboard | MUST |
| F-19 | Fond de carte interchangeable (OSM, Esri x3) | SHOULD |
| F-20 | Import couche shapefile additionnel (ZIP) | COULD |

## 3.2 Hors périmètre V1

- Édition géométrique (dessin/modification sur la carte)
- Module Efficiences (développement séparé)
- Synchronisation temps réel multi-utilisateur
- Application mobile

---

## 4. Inventaire des 15 couches géographiques

> Toutes exposées via `GET /carte/api/couche/<nom>/` en GeoJSON SRID 4326.

### Groupe : Administratif

| Couche | Modèle Django | Type géom | Attributs clés |
|---|---|---|---|
| `provinces` | `carte.Province` | Polygone | nom_fr, nom_ar, superficie_km2, population_totale, temp_moy_annuelle_c, precip_annuelle_mm, et0_annuelle_mm |
| `communes` | `carte.Commune` | Polygone | nom_fr, type_commune (Urbaine/Rurale), population_totale, superficie_km2, nbr_perimetres_agricoles |

### Groupe : Hydrologie

| Couche | Modèle Django | Type géom | Attributs clés |
|---|---|---|---|
| `bassins_versants` | `analyse_hydrologique.BassinVersant` | Polygone | nom, surface (km²), perimetre (km), z_min, z_max, thalweg, ouvrage_en_tete |
| `reseau_hydrographique` | `analyse_hydrologique.ReseauHydrographique` | Polyligne | grid_code (ordre Strahler) |
| `stations_pluvio` | `analyse_hydrologique.StationPluviometrique` | Polygone (Thiessen) | nom, hauteur_moyenne (mm), pjmax_t10/20/50/100 |
| `stations_hydro` | `analyse_hydrologique.StationHydrometrique` | Point | nom, superficie_bv_jaugee, qjmax_t10/20/50/100, debits_mensuels_* (12 valeurs Sep→Août) |
| `stations_clim` | `Besions_Ressources.StationClimatique` | Point | nom, latitude, temperatures_moyennes (JSON 12 val), precipitations_normales (JSON 12 val) |

### Groupe : Diagnostic

| Couche | Modèle Django | Type géom | Attributs clés |
|---|---|---|---|
| `perimetres` | `diagnostic.Perimetre` | Géométrie | ksar_village, commune, superficie_totale, superficie_irriguee, nombre_beneficiaires, statut |
| `seuils` | `diagnostic.Seuil` | Point | nom_du_seuil, nature_du_seuil, type_du_seuil, debit_mobilise (l/s), longueur, hauteur, statut + **EtatSeuil.etat_general** |
| `murs_protection` | `diagnostic.MurProtection` | Géométrie | nom_mur_protection, rive, position, nature_materiaux, longueur, statut |
| `troncons_seguias` | `diagnostic.TronconSeguia` | Géométrie | seguia.nom, troncon (TR1-TR20), longueur, **nature** (béton/terre/…), **debit** (m³/s), efficience_calculee, statut |
| `barrages` | `diagnostic.BarrageRetenue` | Géométrie | nom, capacite_retenue, debit_derive, longueur, hauteur, statut |
| `khettaras` | `diagnostic.Khettara` | Géométrie | nom, debit, longueur, largeur, materiaux_de_construction, statut |
| `forages_puits` | `diagnostic.ForagePuits` | Géométrie | nom, debit (m³/h), profondeur, diametre, source_energie_pompage, statut |
| `prises_locales` | `diagnostic.PriseLocale` | Géométrie | nom, forme_pertuis, debit_derive (m³/s), materiaux_construction, statut |

### Jointures utiles pour le dashboard

```python
# Récupérer état général d'un seuil
Seuil.objects.select_related('diagnostic_etat')

# Récupérer assolement d'un périmètre
Perimetre.objects.prefetch_related('assolement')

# Récupérer bilan d'un périmètre
Perimetre.objects.prefetch_related('bilans_ressources')
```

### Note évolutivité couche tronçons_seguias

Le champ `nature` a pour choix actuels : `béton`, `béton armé`, `terre`, `autre`.
Ces valeurs **peuvent évoluer**. L'endpoint `/carte/api/couche/troncons_seguias/champs/nature/valeurs/`
retourne toujours les valeurs actuelles en base — ne pas les coder en dur dans le JS.
