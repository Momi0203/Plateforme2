---
section: "01"
titre: "Contexte et objectifs"
version: "2.0"
date: "2026-06-04"
tags: [contexte, stack, base-de-données, objectifs]
---

# §1 — Contexte et §2 — Objectifs

## 1.1 Contexte du projet

Plateforme SIG web Django 6 + GeoDjango (PostGIS) pour la gestion des ressources en eau
des périmètres irrigués du Sud-Est marocain (Tafilalet — Midelt / Errachidia).

Quatre domaines métier existants :
- Analyse hydrologique (crues, coefficients Montana)
- Diagnostic des ouvrages hydrauliques (7 types)
- Bilan besoins-ressources en eau (mensuel Sep→Août)
- Géographies de référence (provinces, communes)

Le module Carte est le module transversal manquant.

---

## 1.2 Base de données PostGIS existante

| App Django | Tables principales | Géométries |
|---|---|---|
| `carte` | Province, Commune | PolygonField (SRID 4326) |
| `analyse_hydrologique` | BassinVersant, StationPluviometrique, StationHydrometrique, ReseauHydrographique | PolygonField, PolygonField, PointField, LineStringField |
| `diagnostic` | Perimetre, Seuil, MurProtection, TronconSeguia, BarrageRetenue, Khettara, ForagePuits, PriseLocale | GeometryField / PointField |
| `Besions_Ressources` | StationClimatique, BilanBesoinRessources | PointField |
| `compte` | Utilisateur (rôles) | — |

> Toutes les géométries sont en **SRID 4326**. Les coordonnées métriques X/Y dans
> les champs textuels sont en **EPSG:26191** (Nord Maroc).

### Modèles clés à connaître

```python
# diagnostic/models.py — entité centrale
class Perimetre(models.Model):
    commune = models.ForeignKey('carte.Commune', ...)
    superficie_irriguee = models.FloatField()
    geometrie = gismodels.GeometryField(null=True)
    statut = models.CharField(choices=STATUT_CHOICES)  # non_valide / valide

# Chaque ouvrage a un modèle Etat<X> avec notes 0-5
class EtatSeuil(models.Model):
    seuil = models.OneToOneField(Seuil, primary_key=True)
    etat_general = models.CharField(choices=ETAT_CONSTRUCTION_DIAG_CHOICES)
    # 10 critères notés 0-5 (NOTE_CHOICES)
    etat_structurel_digue = models.IntegerField(choices=NOTE_CHOICES)
    affouillement_aval = models.IntegerField(choices=NOTE_CHOICES)
    # ... (8 autres)

# analyse_hydrologique/models.py
class ReseauHydrographique(models.Model):
    grid_code = models.IntegerField()  # ordre de Strahler
    geometrie = gis_models.LineStringField(srid=4326)
```

### Échelles de notation (communes à tous les Etat<X>)

```python
ETAT_CONSTRUCTION_DIAG_CHOICES = [
    ('t_mauvais', 'Très mauvais'), ('mauvais', 'Mauvais'),
    ('moyen_mauvais', 'Moyen-mauvais'), ('moyen', 'Moyen'),
    ('moyen_bon', 'Moyen-bon'), ('bon', 'Bon'), ('excellent', 'Excellent'),
]

NOTE_CHOICES = [(0,'Absence/aucun'), (1,'Très faible'), (2,'Faible'),
                (3,'Moyen'), (4,'Dégradé'), (5,'Grave/critique')]
```

---

## 1.3 Pile technologique

| Composant | Technologie |
|---|---|
| Framework web | Django 6.0.4 |
| Base de données | PostgreSQL 15 + PostGIS |
| GIS back-end | GeoDjango (`django.contrib.gis`) |
| Rendu carte front-end | MapLibre GL JS |
| Graphiques | Chart.js |
| Export PDF/carte | WeasyPrint ou reportlab |
| Export Excel | openpyxl (déjà installé) |
| GIS natif (Windows) | GDAL 3.12 / GEOS / PROJ — OSGeo4W |
| Auth | `compte.Utilisateur` (AbstractUser + rôle) |

---

## 2.1 Objectif général

Offrir une vue cartographique unifiée permettant de :
- Visualiser toutes les couches PostGIS
- Interroger les entités (requêtes attributaires et spatiales)
- Analyser (outils géospatiaux + boîtes métier)
- Restituer sous 3 formes : **carte / dashboard / tableau**

---

## 2.2 Objectifs spécifiques

| ID | Objectif |
|---|---|
| OBJ-1 | Afficher en superposition toutes les couches géographiques de la base PostGIS |
| OBJ-2 | Contrôle fin de la visualisation (visibilité, ordre, symbologie personnalisée) |
| OBJ-3 | Sélection et requête attributaire et spatiale simples et multicritères |
| OBJ-4 | Outils d'analyse géospatiale (tampon, intersection, proximité, stats) |
| OBJ-5 | Trois modes de restitution synchronisés : carte exportable, dashboard, tableau |
| OBJ-6 | Export en formats imprimables (PDF A4–A0) et numériques (PNG, CSV, Excel, GeoJSON) |
| OBJ-7 | Respect de la matrice des rôles existante (visiteur / opérateur / éditeur) |
