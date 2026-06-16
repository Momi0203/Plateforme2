# Phase — Labels au centre des polygones

**Date :** 12 juin 2026
**Module :** Carte (`carte/`)
**Fichiers touchés :** `carte/static/carte/js/map.js`, `layers.js`, `query.js`,
`contextmenu.js`, `carte/api_views.py`

---

## 1. Objectif

Afficher, pour les couches contenant des **polygones**, le **nom de chaque
entité au centre du polygone** (provinces, communes, bassins versants,
périmètres, et tout ouvrage dont la géométrie est surfacique).

Les couches **ponctuelles** (stations, seuils…) et **linéaires** (réseau
hydrographique) ne reçoivent **pas** de label centré — conforme à la demande
(« les couches qui contiennent des polygones »).

---

## 2. Principe technique

MapLibre place automatiquement un label `symbol` au **centroïde** (pôle
d'inaccessibilité) d'un polygone quand on ajoute un layer `type: 'symbol'` avec
`text-field` sur la même source GeoJSON.

Pour chaque couche chargée **en `fill`** (= polygone), `layers.js` crée un 3ᵉ
sous-layer en plus du fond et du contour :

| Sous-layer | Type | Rôle |
|---|---|---|
| `lyr-<nom>`         | fill   | Remplissage du polygone |
| `lyr-<nom>-outline` | line   | Contour (fill-outline-width n'existe pas en MapLibre) |
| `lyr-<nom>-label`   | symbol | **Nom de l'entité au centre** *(nouveau)* |

### Champ affiché (`label_field`)

Le texte vient du champ **`label_field`** exposé par l'API `liste_couches`.
Par convention, c'est le **premier champ déclaré** dans `LAYER_REGISTRY`
(toujours le « nom » de l'entité), avec possibilité de surcharge explicite via
une clé `"label_field"` dans le registre.

Résolution effective par couche surfacique :

| Couche | label_field |
|---|---|
| provinces / communes | `nom_fr` |
| bassins_versants | `nom` |
| perimetres | `ksar_village` |
| murs_protection | `nom_mur_protection` |
| troncons_seguias | `troncon` |
| barrages / khettaras / forages_puits / prises_locales | `nom` |

---

## 3. Pré-requis : serveur de glyphes

Un layer `symbol` avec `text-field` **exige une URL `glyphs`** dans le style
MapLibre (les polices sont servies en PBF). Le style initial n'en avait pas →
ajout dans `map.js` :

```js
style: {
  version: 8,
  glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
  ...
}
```

Police utilisée : `['Open Sans Regular', 'Noto Sans Regular']` (la 2ᵉ sert de
repli au niveau du glyphe). Dépendance réseau cohérente avec le basemap OSM,
déjà chargé depuis Internet.

> `basemap.js` change de fond en retirant/réajoutant **seulement** le layer
> raster `osm-bg` (pas de `setStyle`) → les glyphs et les labels survivent au
> changement de fond de carte.

---

## 4. Style du label

```js
MAP.addLayer({
  id: `lyr-${nom}-label`,
  type: 'symbol',
  source: `src-${nom}`,
  minzoom: 7,                       // pas de labels quand on dézoome trop
  layout: {
    visibility,
    'text-field':         ['to-string', ['coalesce', ['get', labelField], '']],
    'text-font':          ['Open Sans Regular', 'Noto Sans Regular'],
    'text-size':          12,
    'text-max-width':     8,
    'symbol-placement':   'point',  // 1 label au centroïde du polygone
    'text-allow-overlap': false,    // collision auto → pas de chevauchement
  },
  paint: {
    'text-color':      '#1A1A2E',
    'text-halo-color': '#ffffff',
    'text-halo-width': 1.4,         // halo blanc → lisible sur le remplissage
  },
});
```

- `coalesce(..., '')` : une valeur `null` donne un label vide (non rendu).
- `text-allow-overlap: false` : MapLibre masque les labels qui se chevauchent
  (priorité automatique) → pas de bouillie de texte quand c'est dense.
- `minzoom: 7` : la carte démarre au zoom 9, les labels sont donc visibles
  d'emblée mais disparaissent si l'on dézoome beaucoup.

---

## 5. Cohérence visibilité / filtre

Le label suit **systématiquement** le sort du polygone. Un helper centralise la
bascule de visibilité dans `layers.js` :

```js
function _setCoucheVisibility(nom, vis) {
  for (const suffix of ['', '-outline', '-label']) {
    const id = `lyr-${nom}${suffix}`;
    if (MAP.getLayer(id)) MAP.setLayoutProperty(id, 'visibility', vis);
  }
}
```

Utilisé partout où la visibilité change : `loadLayer` (recharge), `hideLayer`,
isolation (masquer les autres / afficher la cible), `_restoreIsolation`.

Le **filtre de requête** (`applyLayerFilter` / `clearLayerFilter` dans
`query.js`) et le **masque du menu contextuel** (`contextmenu.js`) appliquent
désormais le `setFilter` aux trois sous-layers → quand une requête filtre les
entités, les labels des entités masquées disparaissent aussi.

---

## 6. Fichiers modifiés

| Fichier | Modification |
|---|---|
| `carte/static/carte/js/map.js` | Ajout de `glyphs` dans le style MapLibre. |
| `carte/api_views.py` | `liste_couches` expose `label_field` (défaut = 1er champ déclaré). |
| `carte/static/carte/js/layers.js` | Création du layer `lyr-<nom>-label` pour les couches `fill`. Helper `_setCoucheVisibility()` + refactor des 5 bascules de visibilité pour inclure le label. |
| `carte/static/carte/js/query.js` | `applyLayerFilter` / `clearLayerFilter` filtrent aussi `-label`. |
| `carte/static/carte/js/contextmenu.js` | Masque (`_applyMasque`) et reset filtrent aussi `-label`. |

Aucune migration, aucun changement de modèle.

---

## 7. Tests manuels

1. **Ctrl+F5** pour vider le cache.
2. Au chargement : *Communes* (visible par défaut) affiche le nom de chaque
   commune au centre, avec halo blanc.
3. Cocher *Bassins versants* / *Provinces* / *Périmètres* → noms centrés.
4. Vérifier qu'une couche **ponctuelle** (Stations, Seuils) et **linéaire**
   (Réseau hydrographique) **n'ont pas** de label centré.
5. Dézoomer fortement → les labels disparaissent sous le zoom 7.
6. Décocher une couche → ses labels disparaissent ; recocher → ils reviennent.
7. **Isoler** une couche (œil) → seuls ses labels restent ; réinitialiser → tout revient.
8. **Requête** (entonnoir) qui filtre des entités → seuls les labels des
   entités filtrées restent affichés ; *Réinitialiser le filtre* → tout revient.
9. Changer de **fond de carte** (Satellite) → les labels restent visibles.

---

## 8. Limites et points d'attention

- **Dépendance au serveur de glyphes** `fonts.openmaptiles.org`. S'il est
  injoignable, le texte ne s'affiche pas (le reste de la carte fonctionne). En
  cas de besoin hors-ligne, héberger les PBF localement et pointer `glyphs`
  dessus.
- **Ordre de superposition** : le label d'une couche peut passer sous le
  remplissage (30 % d'opacité) d'une couche chargée après elle → texte
  légèrement atténué, jamais totalement masqué. Non corrigé (cosmétique).
- **Couches `Geometry` mixtes** : le label n'est ajouté que si la **première**
  entité est un polygone (détermine `layerType = 'fill'`). Une couche mêlant
  points et polygones ne sera étiquetée que si elle se charge en `fill`.
- Le label utilise toujours le 1er champ déclaré ; pour en changer sans toucher
  l'ordre des `fields`, ajouter `"label_field": "<champ>"` à l'entrée du
  registre dans `carte/layers.py`.
