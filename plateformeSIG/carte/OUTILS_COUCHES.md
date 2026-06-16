# Box « Couches » — panneau droit Outils de la Carte (Lot E)

La box **Couches** active à la demande un groupe de couches « ouvrage de tête »
**masquées** par défaut, et fournit l'outil **« Réseau du BV »**. Elle remplace
l'ancien outil « Bassins versants & réseau » de la box Hydrologie.

> Contrôleur : [static/carte/js/outils-couches.js](static/carte/js/outils-couches.js).

---

## 1. Outil « Hydrologie 2 — couches ouvrage de tête »

- **But** : injecter, dans le **panneau gauche**, un groupe **« Réseaux ouvrage
  de tête »** que l'utilisateur affiche/masque. Re-cliquer désactive (retrait du
  groupe + déchargement).
- **Données** : `GET /carte/api/couches/activables/` → les couches avec le flag
  `groupe_activable` dans `LAYER_REGISTRY` (toutes `hidden`).
- **6 couches** :
  - `bv_ouvrage_tete` (`analyse_hydrologique.BassinVersant`, 146 polygones) :
    **ligne couche standard** — case à cocher (chargement normal), symbologie,
    requête, sélection, centrer, isoler (via les handlers délégués existants).
  - `reseau_tete_ziz / moulouya / guir / rheris / maider`
    (`carte.ReseauOuvrageTete<Bassin>`, LineString) : couches **volumineuses**
    (Ziz ~152k, Moulouya ~82k tronçons) → **« intersection-only »** : pas de case
    à cocher (jamais chargées en entier), bouton **« Réseau du BV »** à la place
    du multicritère.
- **Injection** : le gabarit de ligne `window.coucheRowHtml(c)` (exposé par
  `map.js`) gère la variante `reseau_tete`. Les métadonnées sont fusionnées dans
  `window.COUCHES_META`.

## 2. Outil « Réseau du BV » (intersection forcée — Q5-bis)

- **But** : afficher une couche réseau **clippée à un bassin versant**.
- **Mode forcé** : on respecte la **couche réseau cliquée** (pas d'appariement
  automatique des 5 bassins). On ne reprend que l'**étape 3** de la logique
  `analyse_hydrologique._reseau_ouvrage_tete_pour_bv` : filtre
  `bboverlaps + intersects` du BV + **filtrage grid_code adaptatif**
  (`RESEAU_SEUIL_INTERSECTION_M2 = 500 km²` : petit BV → réseau complet ; grand
  BV → drains forts `grid_code ≥ 1`, repli sur tout si vide). Override possible
  via « Détail réseau » (`min_grid_code`).
- **Données** :
  `GET /carte/api/reseau-ouvrage-tete/?reseau=<couche>&bv=<pk>&min_grid_code=`
  → GeoJSON `{grid_code, geometry}` + `{ reseau, bv, count, grid_max }`.
- **Rendu** : couche WebGL de lignes **graduées par `grid_code`** (couleur +
  épaisseur), via **`CarteRendu` slot `contexte`** (cohabite avec un résultat
  thématique). Cadrage sur l'emprise des tronçons.
- ⚠ Si la couche réseau cliquée ne couvre pas le BV choisi → résultat vide
  (volontaire, mode forcé).

---

## État des données

| Réseau | Lignes en base |
|---|---|
| Ziz | ~152 671 ✅ |
| Moulouya | ~82 038 ✅ |
| Guir / Rhéris / Maïder | **0** (shapefiles à importer — `import_reseau_<bassin>`) |

Les 3 bassins vides apparaissent dans le groupe mais renvoient 0 tronçon tant que
leurs shapefiles ne sont pas déposés dans
`plateformeSIG/static/resaux hydrographique ouvrage en tete/`.

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| [carte/layers.py](layers.py) | 5 couches réseau + flags `groupe_activable` / `reseau_tete`. |
| [carte/api_views.py](api_views.py) | `couches_activables`, `reseau_ouvrage_tete`. |
| [carte/urls.py](urls.py) | `api/couches/activables/`, `api/reseau-ouvrage-tete/`. |
| [carte/static/carte/js/map.js](static/carte/js/map.js) | `window.coucheRowHtml` (gabarit de ligne + variante réseau). |
| [carte/static/carte/js/outils-couches.js](static/carte/js/outils-couches.js) | Box Couches : activation + « Réseau du BV ». |
| `templates/carte/index.html` | Box « Couches » + sous-panneau `co-panel-reseau`. |
