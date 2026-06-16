# Phase — Symbologie graduée (champs quantitatifs)

**Date :** 12 juin 2026
**Module :** Carte (`carte/`)
**Fichiers touchés :** `carte/api_views.py`, `carte/urls.py`,
`carte/static/carte/js/symbologie.js`, `templates/carte/index.html`

---

## 1. Problème corrigé

Le mode **Catégorisé** de la symbologie traitait tous les champs comme
qualitatifs : une couleur par valeur distincte, plafonnée à 20. Pour un champ
**quantitatif** (debit, longueur, superficie_km2…), chaque nombre est une
valeur distincte → 20 couleurs arbitraires tronquées, sans sens cartographique.

Le mode **Simple** n'a pas été modifié (exigence utilisateur). Le comportement
qualitatif existant est conservé tel quel.

## 2. Choix validés par l'utilisateur

1. **Rendu gradué « taille + couleur au choix »** — deux cases à cocher
   (graduer l'épaisseur/rayon, graduer la couleur), l'une, l'autre ou les deux.
2. **Deux méthodes de classification** — Quantiles (défaut) + Intervalles égaux.
3. **Bornes supérieures éditables** à la main, comme dans QGIS.

## 3. Fonctionnement

### Détection du type de champ (serveur)

Nouvelle API `GET /carte/api/couche/<nom>/champs/<champ>/stats/?classes=n`
(`stats_champ` dans [api_views.py](carte/api_views.py)) :

- Type lu sur le modèle Django : `IntegerField` / `FloatField` / `DecimalField`
  → **quantitatif** ; champ à `choices`, FK, texte, ou `etat_general` virtuel
  → **qualitatif**.
- Quantitatif → renvoie `{type, min, max, count, breaks: {quantiles, egaux}}`
  où `breaks` sont les **bornes supérieures** des n classes (1 ≤ n ≤ 10,
  défaut 5), dernière borne = max.
- Quantiles calculés par interpolation linéaire des percentiles (toutes les
  valeurs non-null triées — volumes faibles, max ~1207).
- **Dédoublonnage croissant** des bornes : les quantiles d'un champ entier à
  faible cardinalité (ex. `sorder` ∈ 1..5) produisent des bornes identiques →
  elles sont fusionnées (le nombre de classes effectif peut être < n demandé).
- Sécurité SEC-05 : seuls les champs déclarés dans `LAYER_REGISTRY` (403 sinon).

### Branchement dans le panneau (JS)

`_loadValeurs` ([symbologie.js](carte/static/carte/js/symbologie.js)) interroge
d'abord `/stats/` :

- **qualitatif** → `_loadValeursQualitatif` (code historique inchangé,
  expression `match`).
- **quantitatif** → `_initGradue` : UI graduée. L'état `_grad` non-null fait
  basculer le bouton « Appliquer » vers `_applyGradue`.

### UI graduée

- **Classes** : 3–7 (défaut 5) — changer recharge les bornes depuis l'API.
- **Méthode** : Quantiles / Intervalles égaux — bascule sans re-fetch (les deux
  jeux de bornes sont renvoyés ensemble).
- **Rendu selon la géométrie** :

| Géométrie | Options |
|---|---|
| Polyligne | ☑ Graduer l'épaisseur (min→max px, défaut 1→8) · ☐ Graduer la couleur (rampe) |
| Point | ☑ Graduer le rayon (défaut 3→14) · ☐ Graduer la couleur |
| Polygone | Rampe de couleur uniquement (toujours active) — choroplèthe |

- Rampe par défaut : `#fdeedd` (clair) → couleur du groupe de la couche.
- **Tableau de classes** comme QGIS : aperçu du symbole (trait d'épaisseur
  croissante / rond / carré coloré) · borne sup **éditable**
  (`input type=number`) · étiquette auto (`≤ b1`, puis `b1 – b2`).
- Tout changement (bornes, min/max de taille, rampe) rafraîchit les aperçus
  et étiquettes en direct sans reconstruire les inputs (focus préservé).

### Application (MapLibre `step`)

- Validation : bornes numériques **strictement croissantes**, au moins un rendu
  coché — sinon message d'erreur sous le tableau.
- Entrée : `['to-number', ['get', champ], min]` ; stops = bornes 1..n-1.
- Couleur → `props.color` du layer + synchro du contour `-outline` (polygones).
- Taille → `line-width` ou `circle-radius`.
- Outputs interpolés linéairement (taille : min→max ; couleur : `_lerpColor`).

### Réinitialiser

Le bouton ↺ existant remet la couleur du groupe **et désormais la taille par
défaut** (`line-width: 1`, `circle-radius: 5`) — il annule donc aussi une
graduation de taille.

## 4. Tests effectués

Vue testée via `RequestFactory` (script temporaire supprimé) :

- `reseau_hydrographique.sorder` → quantitatif, quantiles dédoublonnés
  `[1, 2, 3, 5]` (4 classes effectives), égaux `[1.8, 2.6, 3.4, 4.2, 5]`.
- `bassins_versants.superficie_km2`, `communes.superficie_km2` → bornes OK.
- `communes.type_commune`, `troncons_seguias.nature` (choices),
  `seuils.etat_general` (virtuel) → qualitatif.
- Champ non exposé → 403.
- `manage.py check` : aucun problème.

## 5. Tests manuels à faire (Ctrl+F5)

1. Palette → *Réseau hydrographique* → Catégorisé → champ `sorder` → l'UI
   graduée apparaît (épaisseur cochée). Appliquer → traits d'épaisseur
   croissante comme l'image QGIS de référence.
2. Même couche, cocher aussi « Graduer la couleur » → épaisseur + rampe.
3. *Communes* → `superficie_km2` → rampe de couleur (choroplèthe), 5 classes,
   basculer Quantiles ↔ Intervalles égaux, éditer une borne → étiquettes maj.
4. *Communes* → `type_commune` → l'UI **qualitative historique** (une couleur
   par valeur) s'affiche, inchangée.
5. Bouton ↺ → retour au style par défaut (couleur ET épaisseur/rayon).
6. Mode **Simple** : vérifier qu'il est strictement identique à avant.

## 6. Correctif post-livraison — collisions de noms globales

**Symptôme** : dans Catégorisé, choisir un champ ne chargeait plus rien (le
panneau restait sur « Sélectionnez un champ… », Appliquer grisé).

**Cause** : les JS de la carte sont des scripts classiques qui partagent le
scope global `window`. Deux fichiers déclaraient une fonction homonyme — le
fichier chargé en dernier écrase silencieusement l'autre :

| Fonction | Victime (chargée avant) | Écrasée par | Effet |
|---|---|---|---|
| `_loadValeurs` | symbologie.js | multiquery.js | sélection d'un champ → TypeError silencieuse (signatures différentes) |
| `_esc` | symbologie.js | dashboard.js | échappement des valeurs catégorisées |
| `_flatCoords` | layers.js | table.js | calcul de bbox des features |

**Correction** : renommage préfixé dans les fichiers victimes —
`_symLoadValeurs`, `_symEsc` (symbologie.js), `_lyrFlatCoords` (layers.js).
Scan automatisé des déclarations top-level de tous les JS : plus aucun doublon.

**Règle pour la suite** : préfixer les helpers top-level par module
(`_sym*`, `_lyr*`, `_rm*`, …) ou vérifier l'unicité du nom dans
`carte/static/carte/js/` avant d'ajouter une fonction globale.

## 7. Limites connues

- Les entités à valeur **null** passent par `to-number` → classées comme 0
  (donc dans la classe contenant 0). Rare dans les données ; à raffiner avec
  une couleur « non renseigné » si besoin.
- La sémantique des bornes est `classe i = [b(i-1), b(i))` côté MapLibre
  (`step` utilise ≥), alors que l'étiquette affiche `≤` — l'écart ne concerne
  que les valeurs exactement égales à une borne.
- La pastille de légende de la liste des couches reste sur la dernière couleur
  unie (les expressions sont ignorées par `_livePreviewFromLayer`, comportement
  existant du mode catégorisé).
- `couches_styles.js` (SY-08/SY-09, tronçons de séguias) applique son propre
  style au chargement ; une symbologie graduée appliquée ensuite le remplace —
  le ↺ revient au défaut générique, pas au style SY-08.
