# Plan — Double-clic gauche & Menu contextuel clic droit

> **Statut : EN ATTENTE DE VALIDATION** — ne pas coder avant approbation.
> Mise à jour 2026-06-11 v2 : vérification des valeurs réelles x/y en base, corrections SRID.

---

## Réponses aux questions ouvertes

| Q | Question | Réponse | Impact sur le code |
|---|---|---|---|
| Q1 | Nom du champ `id` dans les GeoJSON | **les deux** : `id` (propriété MapLibre) et `pk` (propriété JSON) | Filtre : `['in', ['get', 'id'], ...]` — à confirmer avec la vue API |
| Q2 | Périmètres sans commune exclus du masque Province/Commune ? | **Oui** | Queryset `filter(commune__province_id=pk)` les exclut naturellement |
| Q3 | Géométries des ouvrages liés au périmètre ? | **Tous ont** un champ `geometrie` (voir table ci-dessous) | Intersection possible pour tous |
| Q4 | StationClimatique : Point ? | **Oui** (Point SRID 4326). StationPluvio : Polygon zone influence **ne pas utiliser** pour l'intersection — utiliser les coords `x`/`y` Nord Maroc avec `ST_Transform` | Requête spéciale pour stations_pluvio |
| Q5 | Question SRID | Expliqué ci-dessous | Toutes les géométries DB sont SRID 4326 sauf `x`/`y` de StationPluvio |

---

### Réponse à la question SRID (après vérification en base)

**SRID** = Identifiant du Système de Référence de Coordonnées (code EPSG).

| SRID | Nom | Unité | Concerne |
|---|---|---|---|
| **4326** | WGS84 (GPS / Google Maps) | degrés décimaux (longitude, latitude) | Toutes les géométries Django en DB |
| **26191** | Lambert Nord Maroc | mètres (Est, Nord) | Uniquement les champs `x`/`y` de StationHydrometrique |

**Résultat de la vérification réelle (exécutée sur la base)** :

| Modèle | Champ `x` | Champ `y` | Système réel | Champ géométrie existant |
|---|---|---|---|---|
| `StationPluviometrique` | `-4.507978` (lon WGS84) | `32.144766` (lat WGS84) | **WGS84 degrés** (SRID 4326) | `geometrie` = Polygon Thiessen (OK) — **pas de Point** |
| `StationHydrometrique` | `599017.84` (Est Lambert) | `172352.191` (Nord Lambert) | **Lambert Nord Maroc** (SRID 26191) | `geometrie` = Point WGS84 **déjà rempli** |

> ⚠️ Le `verbose_name` de `StationPluviometrique.x/y` dit « Nord Maroc, m » mais les valeurs réelles sont en degrés WGS84 — c'est une erreur de documentation dans les modèles.

**Conséquences :**
- `StationHydrometrique` → utiliser `geometrie` (Point WGS84) directement. Pas de conversion nécessaire.
- `StationPluviometrique` → `x`/`y` sont WGS84 degrés. Pour afficher un Point sur la carte et pour l'intersection BV, il faut soit :
  - **Ajouter un champ** `geom_point = PointField(srid=4326, null=True)` (migration + data migration `ST_SetSRID(ST_MakePoint(x, y), 4326)`)
  - **Ou** utiliser SQL brut `ST_SetSRID(ST_MakePoint(x, y), 4326)` dans la vue (sans migration)

### Nouvelle tâche T0 — Afficher stations_pluvio en Points

**Problème** : `stations_pluvio` est actuellement affiché comme Polygon Thiessen. L'utilisateur veut les Points de station.

**Solution retenue** : ajouter `geom_point` PointField + migration data.

**Migration Django** (dans `analyse_hydrologique`) :
```python
# Champ ajouté
geom_point = gis_models.PointField(srid=4326, null=True, blank=True,
                                    verbose_name="Géométrie point (WGS84)")
```

**Data migration** :
```python
# x et y étant déjà en WGS84 degrés (lon, lat) :
from django.contrib.gis.geos import Point
for s in StationPluviometrique.objects.all():
    if s.x and s.y:
        s.geom_point = Point(s.x, s.y, srid=4326)
        s.save(update_fields=['geom_point'])
```

**Mise à jour LAYER_REGISTRY** (`carte/layers.py`) :
```python
"stations_pluvio": {
    ...
    "geom_field": "geom_point",   # était "geometrie" (Polygon Thiessen)
    "geom_type":  "Point",        # était "Polygon"
    ...
}
```

**Intersection BV (T5) pour stations_pluvio** — simple, pas de ST_Transform :
```python
('bassins_versants', 'stations_pluvio'):
    lambda pk: StationPluviometrique.objects.exclude(geom_point__isnull=True).filter(
        geom_point__intersects=BassinVersant.objects.get(pk=pk).geometrie
    ),
```

---

### Table des géométries des ouvrages (Q3)

| Couche (LAYER_REGISTRY) | Modèle Django | Champ géométrie | Type géométrie réel | SRID | Nullable |
|---|---|---|---|---|---|
| `perimetres` | `diagnostic.Perimetre` | `geometrie` | GeometryField | 4326 | oui |
| `seuils` | `diagnostic.Seuil` | `geometrie` | PointField | 4326 | oui |
| `murs_protection` | `diagnostic.MurProtection` | `geometrie` | PointField | 4326 | oui |
| `troncons_seguias` | `diagnostic.TronconSeguia` | `geometrie` | **LineStringField** | 4326 | oui |
| `barrages` | `diagnostic.BarrageRetenue` | `geometrie` | PointField | 4326 | oui |
| `khettaras` | `diagnostic.Khettara` | `geometrie` | PointField | 4326 | oui |
| `forages_puits` | `diagnostic.ForagePuits` | `geometrie` | PointField | 4326 | oui |
| `prises_locales` | `diagnostic.PriseLocale` | `geometrie` | PointField | 4326 | oui |
| `stations_pluvio` | `analyse_hydrologique.StationPluviometrique` | `geometrie` | PolygonField (zone Thiessen) | 4326 | oui |
| `stations_hydro` | `analyse_hydrologique.StationHydrometrique` | `geometrie` | PointField | 4326 | oui |
| `stations_clim` | `Besions_Ressources.StationClimatique` | `geometrie` | PointField | 4326 | oui |
| `bassins_versants` | `carte.BassinVersant` | `geometrie` | PolygonField | 4326 | oui |
| `reseau_hydrographique` | `carte.ReseauHydrographique` | `geometrie` | LineStringField | 4326 | non |

> **Note stations_pluvio** : La couche affiche le polygone Thiessen sur la carte. Pour l'intersection BV, on utilise le point de localisation calculé depuis `x`, `y` (EPSG:26191) via `ST_Transform`. Ne jamais utiliser le polygone `geometrie` pour l'intersection BV.

> **Note géométries nullables** : Tous les ouvrages peuvent avoir `geometrie = NULL`. Les filtres FK (hiérarchie 1) ne sont pas affectés. Pour la hiérarchie 2 (intersection), ajouter `.exclude(geometrie__isnull=True)`.

---

## Périmètre des tâches

| # | Tâche | Fichier(s) concerné(s) |
|---|---|---|
| **T0** | **Pré-requis** — Ajouter `geom_point` PointField à `StationPluviometrique` + data migration + LAYER_REGISTRY | `analyse_hydrologique/models.py`, migration, `carte/layers.py` |
| T1 | Double-clic gauche → zoom vers l'entité cliquée | `layers.js` |
| T2 | Squelette HTML/CSS du menu contextuel clic droit | `index.html` |
| T3 | Action « Zoom vers l'entité » dans le menu clic droit | `contextmenu.js` (nouveau) |
| T4 | Action « Masque » — hiérarchie 1 (Province → Commune → Périmètre → Ouvrages) | `contextmenu.js` + `views.py` + `urls.py` |
| T5 | Action « Masque » — hiérarchie 2 (Bassin Versant) | `contextmenu.js` + `views.py` + `urls.py` |
| T6 | Bannière « masque actif » + bouton réinitialisation | `contextmenu.js` + `index.html` |

---

## T1 — Double-clic gauche : zoom vers l'entité

### Comportement actuel
Aucun handler dédié. MapLibre applique son zoom natif (niveau +1), ce qui est incorrect.

### Comportement cible
Double-clic sur une entité → `MAP.fitBounds()` sur l'emprise exacte de cette entité.

### Implémentation

Dans `loadLayer()` de `layers.js`, juste après les listeners `mouseenter/mouseleave` :

```js
MAP.on('dblclick', `lyr-${nom}`, e => {
  e.preventDefault();          // annule le zoom natif MapLibre
  const feat = e.features?.[0];
  if (!feat) return;
  MAP.fitBounds(_bboxOfFeature(feat.geometry), { padding: 60, maxZoom: 16 });
});
```

Fonctions utilitaires `_bboxOfFeature` et `_flatCoords` (haut de `layers.js`) :

```js
function _bboxOfFeature(geom) {
  const coords = _flatCoords(geom);
  const lons = coords.map(c => c[0]);
  const lats = coords.map(c => c[1]);
  const pad = geom.type === 'Point' ? 0.015 : 0;  // ~1.5 km autour d'un point
  return [[Math.min(...lons) - pad, Math.min(...lats) - pad],
          [Math.max(...lons) + pad, Math.max(...lats) + pad]];
}
function _flatCoords(geom) {
  if (geom.type === 'Point') return [geom.coordinates];
  const src = geom.geometries ?? geom.coordinates;
  if (geom.type === 'GeometryCollection') return src.flatMap(_flatCoords);
  return src.flat(Infinity).reduce(
    (a, _, i, arr) => i % 2 === 0 ? [...a, [arr[i], arr[i+1]]] : a, []
  );
}
```

---

## T2 — Squelette HTML/CSS du menu contextuel

### HTML (inséré dans `#zone-carte` de `index.html`)

```html
<div id="carte-ctx-menu">
  <div class="ctx-header" id="ctx-layer-name"></div>
  <button class="ctx-item" id="ctx-action-zoom">
    <i class="fas fa-search-plus"></i> Zoom vers l'entité
  </button>
  <hr class="ctx-sep">
  <div class="ctx-item ctx-has-sub" id="ctx-masque-trigger">
    <i class="fas fa-filter"></i> Masque
    <i class="fas fa-chevron-right" style="margin-left:auto;font-size:9px"></i>
  </div>
  <div id="ctx-masque-sub"></div>  <!-- sous-menu généré dynamiquement -->
</div>
```

### CSS (dans `<style>` de `index.html`)

```css
#carte-ctx-menu {
  position: fixed;
  display: none;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-shadow: 0 4px 20px rgba(0,0,0,.22);
  min-width: 200px;
  z-index: 900;
  font-size: 12.5px;
  overflow: hidden;
}
.ctx-header {
  padding: 7px 12px;
  background: var(--c-dark);
  color: #fff;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.ctx-item {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 8px 13px;
  border: none;
  background: transparent;
  font-size: 12.5px;
  font-family: inherit;
  color: var(--c-text);
  cursor: pointer;
  text-align: left;
  transition: background .1s;
}
.ctx-item:hover   { background: #fdf7ef; }
.ctx-item i       { color: var(--c-accent); width: 14px; text-align: center; }
.ctx-sep          { border: none; border-top: 1px solid #f0e8d8; margin: 2px 0; }
.ctx-sub-item     { padding-left: 28px; font-size: 12px; }
.ctx-sub-item:hover { background: #fdf7ef; color: var(--c-dark); }
```

---

## T3 — Action « Zoom vers l'entité » (clic droit)

Identique à T1 : réutilise `_bboxOfFeature()` sur la feature stockée lors de l'ouverture du menu.

---

## T4 — Masque — Hiérarchie 1 (Province → Commune → Périmètre → Ouvrages)

### Schéma des FK (liens en base de données)

```
Province  (carte.Province)
  └── Commune.province ──FK──> Province
        └── Perimetre.commune ──FK──> Commune  [nullable — périmètres sans commune exclus]
              ├── Seuil.perimetre           FK
              ├── MurProtection.perimetre   FK
              ├── BarrageRetenue.perimetre  FK
              ├── Khettara.perimetre        FK
              ├── ForagePuits.perimetre     FK
              ├── PriseLocale.perimetre     FK
              └── TronconSeguia ──FK──> Seguias.perimetre  FK  (2 niveaux)
```

### Sous-menu Masque proposé selon la couche cliquée

| Couche cliquée | Couches inférieures proposées dans le sous-menu |
|---|---|
| `provinces` | communes, perimetres, seuils, murs_protection, troncons_seguias, barrages, khettaras, forages_puits, prises_locales |
| `communes` | perimetres, seuils, murs_protection, troncons_seguias, barrages, khettaras, forages_puits, prises_locales |
| `perimetres` | seuils, murs_protection, troncons_seguias, barrages, khettaras, forages_puits, prises_locales |

### Nouvel endpoint Django

**URL :** `GET /carte/api/masque/<str:couche_parente>/<int:pk>/<str:couche_enfant>/`
**Retour :** `{"pks": [1, 2, 3], "count": 3}`

**Table de routage dans `carte/views.py` :**

```python
from diagnostic.models import (Perimetre, Seuil, MurProtection, BarrageRetenue,
                                Khettara, ForagePuits, PriseLocale, TronconSeguia)
from carte.models import Province, Commune

MASQUE_QUERIES = {
  # Province → …
  ('provinces', 'communes'):
      lambda pk: Commune.objects.filter(province_id=pk),
  ('provinces', 'perimetres'):
      lambda pk: Perimetre.objects.filter(commune__province_id=pk),
  ('provinces', 'seuils'):
      lambda pk: Seuil.objects.filter(perimetre__commune__province_id=pk),
  ('provinces', 'murs_protection'):
      lambda pk: MurProtection.objects.filter(perimetre__commune__province_id=pk),
  ('provinces', 'troncons_seguias'):
      lambda pk: TronconSeguia.objects.filter(seguia__perimetre__commune__province_id=pk),
  ('provinces', 'barrages'):
      lambda pk: BarrageRetenue.objects.filter(perimetre__commune__province_id=pk),
  ('provinces', 'khettaras'):
      lambda pk: Khettara.objects.filter(perimetre__commune__province_id=pk),
  ('provinces', 'forages_puits'):
      lambda pk: ForagePuits.objects.filter(perimetre__commune__province_id=pk),
  ('provinces', 'prises_locales'):
      lambda pk: PriseLocale.objects.filter(perimetre__commune__province_id=pk),
  # Commune → …
  ('communes', 'perimetres'):
      lambda pk: Perimetre.objects.filter(commune_id=pk),
  ('communes', 'seuils'):
      lambda pk: Seuil.objects.filter(perimetre__commune_id=pk),
  ('communes', 'murs_protection'):
      lambda pk: MurProtection.objects.filter(perimetre__commune_id=pk),
  ('communes', 'troncons_seguias'):
      lambda pk: TronconSeguia.objects.filter(seguia__perimetre__commune_id=pk),
  ('communes', 'barrages'):
      lambda pk: BarrageRetenue.objects.filter(perimetre__commune_id=pk),
  ('communes', 'khettaras'):
      lambda pk: Khettara.objects.filter(perimetre__commune_id=pk),
  ('communes', 'forages_puits'):
      lambda pk: ForagePuits.objects.filter(perimetre__commune_id=pk),
  ('communes', 'prises_locales'):
      lambda pk: PriseLocale.objects.filter(perimetre__commune_id=pk),
  # Périmètre → …
  ('perimetres', 'seuils'):
      lambda pk: Seuil.objects.filter(perimetre_id=pk),
  ('perimetres', 'murs_protection'):
      lambda pk: MurProtection.objects.filter(perimetre_id=pk),
  ('perimetres', 'troncons_seguias'):
      lambda pk: TronconSeguia.objects.filter(seguia__perimetre_id=pk),
  ('perimetres', 'barrages'):
      lambda pk: BarrageRetenue.objects.filter(perimetre_id=pk),
  ('perimetres', 'khettaras'):
      lambda pk: Khettara.objects.filter(perimetre_id=pk),
  ('perimetres', 'forages_puits'):
      lambda pk: ForagePuits.objects.filter(perimetre_id=pk),
  ('perimetres', 'prises_locales'):
      lambda pk: PriseLocale.objects.filter(perimetre_id=pk),
}
```

---

## T5 — Masque — Hiérarchie 2 (Bassin Versant)

### Schéma des liens

```
BassinVersant  (carte.BassinVersant — Polygon SRID 4326)
  ├── reseau_hydrographique  :  FK direct (ReseauHydrographique.bassin_versant)
  ├── seuils                 :  FK nullable (Seuil.bassin_versant)  OU  ST_Intersects(geom, bv)
  ├── barrages               :  FK nullable (BarrageRetenue.bassin_versant)  OU  ST_Intersects
  ├── prises_locales         :  FK nullable (PriseLocale.bassin_versant)  OU  ST_Intersects
  ├── stations_hydro         :  ST_Intersects(geometrie Point 4326, bv.geometrie)
  ├── stations_clim          :  ST_Intersects(geometrie Point 4326, bv.geometrie)
  └── stations_pluvio        :  ST_Within(ST_Transform(ST_SetSRID(ST_MakePoint(x, y), 26191), 4326), bv.geometrie)
                                  ⚠️ utilise coords x/y Nord Maroc, PAS le polygone Thiessen
```

### Couches proposées dans le sous-menu

| Couche cliquée | Couches proposées |
|---|---|
| `bassins_versants` | reseau_hydrographique, seuils, barrages, prises_locales, stations_hydro, stations_clim, stations_pluvio |

### Queryset Django pour chaque enfant

```python
from django.db.models import Q
from analyse_hydrologique.models import (BassinVersant, ReseauHydrographique,
                                          StationPluviometrique, StationHydrometrique)
from Besions_Ressources.models import StationClimatique

# Ajout à MASQUE_QUERIES :

('bassins_versants', 'reseau_hydrographique'):
    lambda pk: ReseauHydrographique.objects.filter(bassin_versant_id=pk),

('bassins_versants', 'seuils'):
    lambda pk: Seuil.objects.exclude(geometrie__isnull=True).filter(
        Q(bassin_versant_id=pk) |
        Q(geometrie__intersects=BassinVersant.objects.get(pk=pk).geometrie)
    ),

('bassins_versants', 'barrages'):
    lambda pk: BarrageRetenue.objects.exclude(geometrie__isnull=True).filter(
        Q(bassin_versant_id=pk) |
        Q(geometrie__intersects=BassinVersant.objects.get(pk=pk).geometrie)
    ),

('bassins_versants', 'prises_locales'):
    lambda pk: PriseLocale.objects.exclude(geometrie__isnull=True).filter(
        Q(bassin_versant_id=pk) |
        Q(geometrie__intersects=BassinVersant.objects.get(pk=pk).geometrie)
    ),

('bassins_versants', 'stations_hydro'):
    lambda pk: StationHydrometrique.objects.exclude(geometrie__isnull=True).filter(
        geometrie__intersects=BassinVersant.objects.get(pk=pk).geometrie
    ),

('bassins_versants', 'stations_clim'):
    lambda pk: StationClimatique.objects.exclude(geometrie__isnull=True).filter(
        geometrie__intersects=BassinVersant.objects.get(pk=pk).geometrie
    ),

# stations_pluvio : x,y sont WGS84 degrés → Point(x, y, srid=4326), pas de ST_Transform
# Requiert T0 (champ geom_point ajouté)
('bassins_versants', 'stations_pluvio'):
    lambda pk: StationPluviometrique.objects.exclude(geom_point__isnull=True).filter(
        geom_point__intersects=BassinVersant.objects.get(pk=pk).geometrie
    ),
```

---

## T6 — Bannière masque actif

Nouveau `<div id="carte-masque-banner">` (style identique à `#carte-isolation-banner`) :

```
▼ Masque actif : Seuils de la Province Errachidia — 12 entités     ✕ Réinitialiser
```

**Réinitialisation :**
1. `MAP.setFilter('lyr-${nom}', null)` → retire le filtre MapLibre
2. Restaure la visibilité originale des couches (selon cases à cocher)
3. Cache la bannière

---

## Flux complet — Action Masque (frontend)

```
1. Clic droit sur entité (couche "provinces", pk=3, nom="Errachidia")
        ↓
2. Menu contextuel s'ouvre → "Masque" → sous-menu :
   [Communes] [Périmètres] [Seuils] [Murs] [Tronçons séguias] [Barrages] [Khettaras] [Forages] [Prises]
        ↓
3. Utilisateur clique "Seuils"
        ↓
4. fetch GET /carte/api/masque/provinces/3/seuils/
        ↓
5. Réponse : { "pks": [12, 45, 67], "count": 3 }
        ↓
6. loadLayer('seuils', 'visible')  [si pas déjà chargée]
        ↓
7. MAP.setFilter('lyr-seuils', ['in', ['get', 'id'], ['literal', [12, 45, 67]]])
        ↓
8. Masquer les autres couches non liées
        ↓
9. Afficher bannière : "Masque actif : Seuils de Province Errachidia — 3 entités"
```

---

## Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `analyse_hydrologique/models.py` | **T0** : ajouter `geom_point = PointField(srid=4326, null=True)` à `StationPluviometrique` |
| `analyse_hydrologique/migrations/00XX_...py` | **T0** : migration schema + data migration `Point(x, y, srid=4326)` |
| `carte/layers.py` | **T0** : `stations_pluvio` → `geom_field: "geom_point"`, `geom_type: "Point"` |
| `carte/static/carte/js/layers.js` | **T1** : listener `dblclick` dans `loadLayer()` + fonctions `_bboxOfFeature`/`_flatCoords` |
| `carte/static/carte/js/contextmenu.js` | **Créer** : logique T2/T3/T4/T5/T6 (menu, zoom, masque, bannière) |
| `templates/carte/index.html` | **T2** : HTML `#carte-ctx-menu` + `#carte-masque-banner`, CSS, `<script src="contextmenu.js">` |
| `carte/api_views.py` | **T4/T5** : ajouter vue `masque_enfants()` + dict `MASQUE_QUERIES` |
| `carte/urls.py` | **T4/T5** : ajouter route `api/masque/<couche>/<pk>/<enfant>/` |

**1 migration requise** (T0 : ajout `geom_point` sur `StationPluviometrique`).
**Aucune autre migration.**

---

*Document mis à jour le 2026-06-11.*
