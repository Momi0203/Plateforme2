---
section: "00"
titre: "Résumé exécutif"
version: "2.0"
date: "2026-06-04"
tags: [résumé, contexte, contraintes]
---

# Résumé exécutif — Module Carte

## En une phrase

Développer un module de visualisation et d'analyse géospatiale intégré à la Plateforme SIG
Django/PostGIS existante, pour afficher, interroger et analyser les ouvrages hydrauliques
des périmètres irrigués du Tafilalet (Maroc).

---

## Ce qui existe déjà (ne pas recoder)

```
diagnostic/models.py    → Perimetre + Seuil, Seguia, Barrage, Khettara, Forage, PriseLocale
                           + modèles EtatX (diagnostics notés 0-5)
analyse_hydrologique/   → BassinVersant, StationPluvio, StationHydro, ReseauHydrographique
Besions_Ressources/     → StationClimatique, BilanBesoinRessources (calculs mensuels)
carte/models.py         → Province, Commune (géographies de référence)
compte/models.py        → Utilisateur (rôles : visiteur / opérateur / éditeur)
```

Toutes ces tables ont des champs `geometrie` (SRID 4326) exploitables directement.

---

## Ce qui est à construire

Une nouvelle app Django `carte/` avec :

| Composant | Description |
|---|---|
| `carte/layers.py` | LAYER_REGISTRY — déclaration de toutes les couches |
| `carte/api_views.py` | Endpoints GeoJSON + requêtes + outils + exports |
| `carte/tools.py` | Logique outils géospatiaux (tampon, intersection…) |
| `carte/templates/carte/index.html` | Page principale avec MapLibre GL JS |
| `carte/static/carte/js/` | map.js, layers.js, query.js, dashboard.js, table.js |

---

## Interface — 3 zones

```
┌─────────────┬──────────────────────────────┬──────────────────┐
│  PANNEAU    │     ZONE CENTRALE            │  PANNEAU DROIT   │
│  GAUCHE     │  ┌──────┬─────────┬───────┐  │  (Outils)        │
│  (280px)    │  │Carte │Dashboard│Tableau│  │                  │
│             │  └──────┴─────────┴───────┘  │  Boîtes à outils │
│  Couches    │                              │  métier +        │
│  Sélection  │  MapLibre GL JS              │  génériques      │
│  Requêtes   │  Chart.js                    │                  │
│  Symbologie │  Grille paginée              │  Favoris         │
│  Drill-down │                              │  Récents         │
└─────────────┴──────────────────────────────┴──────────────────┘
```

---

## 5 contraintes à ne jamais oublier

1. **SRID 4326** partout en base — reprojeter en EPSG:26191 pour les calculs métriques
2. **Calendrier Sep→Août** pour toutes les séries mensuelles (12 valeurs)
3. **Évolutivité** — les listes de choix (nature, état, type…) se lisent depuis l'API,
   jamais codées en dur dans le JS
4. **Rôles** — visiteur=lecture seule, opérateur=requêtes+export, éditeur=édition
5. **Ne pas modifier** les modèles des apps existantes depuis `carte/`

---

## Priorités V1

| Priorité | Fonctionnalités |
|---|---|
| **MUST** | Affichage couches, sélection, requête simple, symbologie, export carte PDF, tableau CSV |
| **SHOULD** | Requête multicritère, dashboard, boîtes outils métier, Esri basemaps |
| **COULD** | SQL avancé, bibliothèque de styles, import shapefile |
