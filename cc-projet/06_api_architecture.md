---
section: "06"
titre: "API Django et architecture technique"
version: "2.0"
date: "2026-06-04"
tags: [API, GeoJSON, Django, LAYER_REGISTRY, architecture, performance]
---

# §7 — API Django, §9 — Exigences NF, §10 — Architecture

---

## 7. Endpoints API Django

Préfixe : `/carte/api/`
Implémentation : vues Django standard (`JsonResponse`) — pas de DRF.

### 7.1 Couches GeoJSON

| URL | Méthode | Paramètres | Retour |
|---|---|---|---|
| `/carte/api/couches/` | GET | — | Liste des couches avec métadonnées (nom, type géom, champs, groupe) |
| `/carte/api/couche/<nom>/` | GET | `bbox, srid, limit, offset, fields` | GeoJSON paginé de la couche |
| `/carte/api/couche/<nom>/<pk>/` | GET | — | GeoJSON complet d'une entité |
| `/carte/api/couche/<nom>/extent/` | GET | — | Bounding box (xmin, ymin, xmax, ymax) |

### 7.2 Champs et valeurs (évolutivité)

| URL | Méthode | Retour |
|---|---|---|
| `/carte/api/couche/<nom>/champs/` | GET | Liste des champs avec type et indicateur à choix fermé |
| `/carte/api/couche/<nom>/champs/<champ>/valeurs/` | GET | Valeurs distinctes + libellés depuis CHOICES Django |

> **Ces deux endpoints sont CRITIQUES pour l'évolutivité.** Tout composant front-end
> qui présente des valeurs d'un champ DOIT les lire ici.

### 7.3 Requêtes et sélection

| URL | Méthode | Corps | Retour |
|---|---|---|---|
| `/carte/api/requete/simple/` | POST | `{couche, champ, operateur, valeur}` | `{pks: [...]}` |
| `/carte/api/requete/multicritere/` | POST | `{couche, conditions: [...], logique}` | `{pks: [...]}` |
| `/carte/api/requete/spatiale/` | POST | `{couche, type_spatial, geometrie_ref, distance_m}` | `{pks: [...]}` |

### 7.4 Outils géospatiaux

| URL | Méthode | Description |
|---|---|---|
| `/carte/api/outils/buffer/` | POST | Tampon autour d'une couche ou sélection |
| `/carte/api/outils/intersection/` | POST | Intersection entre deux couches |
| `/carte/api/outils/union/` | POST | Union de deux couches |
| `/carte/api/outils/dissolve/` | POST | Dissolution par champ |
| `/carte/api/outils/near/` | POST | Distance minimale entre couches |
| `/carte/api/outils/stats/` | POST | Statistiques par zone (count, sum, avg, min, max) |
| `/carte/api/outils/efficience/` | POST | Recalcul PI + PV pour tronçons sélectionnés |
| `/carte/api/outils/manning/` | POST | Calcul débit Manning pour tronçons sélectionnés |
| `/carte/api/outils/scoring/` | POST | Score composite (poids utilisateur × notes EtatX) |

### 7.5 Exports

| URL | Méthode | Description |
|---|---|---|
| `/carte/api/export/csv/` | POST | CSV couche ou sélection |
| `/carte/api/export/excel/` | POST | Excel .xlsx |
| `/carte/api/export/geojson/` | POST | GeoJSON |
| `/carte/api/export/carte/` | POST | PDF/PNG, format A4–A0, DPI, éléments layout |
| `/carte/api/export/dashboard/` | POST | PDF/PNG dashboard |

---

## 9. Exigences non fonctionnelles

### 9.1 Performance

| Exigence | Cible |
|---|---|
| Chargement couche légère (< 500 entités) | < 2 s |
| Chargement couche lourde (séguias, réseau hydro) | < 5 s |
| Réponse requête attributaire simple | < 1 s |
| Outil tampon sur 100 entités | < 3 s |
| Génération export PDF A4 300 dpi | < 10 s |
| Rendu carte après zoom/pan | < 1 s |

> Pour les couches volumineuses (réseau hydrographique > 10 000 tronçons),
> envisager MVT via `pg_tileserv` plutôt que GeoJSON.

### 9.2 Compatibilité

- Chrome 120+, Firefox 120+, Edge 120+ (WebGL requis)
- Résolution minimale : 1280 × 720 px
- Responsive tablette (1024 px) — panneaux rétractables

### 9.3 Fiabilité

- Opérations lecture uniquement → jamais de modification en base
- Erreur outil → la carte reste fonctionnelle (pas de crash global)
- Message d'erreur toast + log consultable

---

## 10. Architecture technique

### 10.1 Schéma

```
Navigateur
  MapLibre GL JS (rendu vectoriel)
  Chart.js (graphiques dashboard)
  Fetch API → /carte/api/*
       ↕
Django Views (carte/)
  views.py        → Vue HTML principale
  api_views.py    → JsonResponse / StreamingHttpResponse
  tools.py        → Wrappeurs GDAL/GeoDjango
       ↕
ORM GeoDjango
  .filter(geometrie__intersects=...)
  .annotate(distance=...)
  .transform(srid=26191)   ← pour calculs métriques
       ↕
PostGIS
  ST_Buffer, ST_Intersection, ST_Distance, ST_Simplify
```

### 10.2 LAYER_REGISTRY — concept clé

```python
# carte/layers.py
LAYER_REGISTRY = {
    "seuils": {
        "model": "diagnostic.Seuil",
        "geom_field": "geometrie",
        "geom_type": "Point",
        "groupe": "Diagnostic",
        "label": "Seuils",
        "fields": ["nom_du_seuil", "nature_du_seuil", "debit_mobilise", "statut"],
        "join_etat": "diagnostic_etat",  # OneToOne Etat<X>
    },
    "troncons_seguias": {
        "model": "diagnostic.TronconSeguia",
        "geom_field": "geometrie",
        "geom_type": "LineString",
        "groupe": "Diagnostic",
        "label": "Tronçons de séguias",
        "fields": ["troncon", "nature", "debit", "longueur", "efficience_calculee", "statut"],
    },
    # ... une entrée par couche
}
```

**Ajouter une couche = une entrée dans LAYER_REGISTRY. Aucune modification JS.**

### 10.3 Structure de fichiers à créer

```
plateformeSIG/carte/
├── models.py          ← Province, Commune (existants) + StyleCouche, RequeteNommee (nouveaux)
├── layers.py          ← LAYER_REGISTRY
├── views.py           ← Vue HTML principale /carte/
├── api_views.py       ← Tous les endpoints /carte/api/*
├── tools.py           ← Outils géospatiaux (buffer, intersection, scoring…)
├── serializers.py     ← Sérialisation GeoJSON par couche
├── urls.py            ← Routes
├── templates/carte/
│   └── index.html
├── static/carte/
│   ├── js/
│   │   ├── map.js        ← Initialisation MapLibre GL
│   │   ├── layers.js     ← Chargement GeoJSON dynamique
│   │   ├── query.js      ← Requêtes attributaires
│   │   ├── tools.js      ← Appels API outils
│   │   ├── dashboard.js  ← Chart.js widgets
│   │   └── table.js      ← Tableau attributaire
│   └── css/
│       └── carte.css
└── migrations/
    └── 0001_initial.py   ← StyleCouche + RequeteNommee
```

### 10.4 Nouveaux modèles Django à créer

```python
# carte/models.py (ajouts)

class StyleCouche(models.Model):
    """Bibliothèque de styles personnels de l'utilisateur."""
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nom_couche   = models.CharField(max_length=100)   # clé dans LAYER_REGISTRY
    nom_style    = models.CharField(max_length=100)
    parametres   = models.JSONField()                  # config MapLibre paint
    created_at   = models.DateTimeField(auto_now_add=True)

class RequeteNommee(models.Model):
    """Sauvegarde des requêtes multicritères."""
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nom         = models.CharField(max_length=100)
    couche      = models.CharField(max_length=100)
    expression  = models.JSONField()    # conditions + logique
    created_at  = models.DateTimeField(auto_now_add=True)
```
