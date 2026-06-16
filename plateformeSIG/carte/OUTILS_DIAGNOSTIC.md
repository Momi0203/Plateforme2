# Box « Diagnostic » — panneau droit Outils de la Carte

Documentation des outils de la box **Diagnostic**. Lecture des modèles
`diagnostic` (ouvrages, `Etat<X>`, `Assolement`) et réutilisation des outils
de scoring existants. Rendus carte via **`CarteRendu`**.

> **Mises à jour Lots A–G** :
> - **Indice de priorité / Scoring** (cas extrême point 1) : on garde le choix de
>   couche **et** on restreint à la **sélection carte** (`pks` envoyés à
>   `/outils/scoring/` et `/outils/indice-priorite/`).
> - **Comparaison d'état** et **Débit mobilisé** : couche conservée +
>   **sélection carte** (`&pks=`). Comparaison d'état en **`FloatingChart`** ;
>   Débit mobilisé avec **modes** (point 4 : cercles proportionnels / classés).
> - **Assolement** : menu supprimé → **sélection carte** d'un périmètre ;
>   `FloatingChart`.
> - Backend : filtrage `pks` ajouté à `etat_comparaison` et `indice_priorite`.

---

## 1. Indice de priorité / Scoring (carte)

- **But** : noter et colorer les ouvrages d'une couche selon des critères
  d'état pondérés.
- **Module** : carte, **slot `resultat`** — recoloration de `lyr-<couche>` avec
  la **bonne propriété** selon la géométrie (`circle-color` pour les points,
  `line-color` pour les tronçons).
- **Sélection** : couche d'ouvrages + critères (`Etat<X>`) avec coefficients
  0–5 + **méthode**.
- **Méthodes** :
  - **Seuils fixes** → `POST api/outils/indice-priorite/` (indice 0–100 %, 5 classes).
  - **Quantiles / Jenks** → `POST api/outils/scoring/` (breaks calculés).
- **Critères** : `GET api/couche/<nom>/criteres/`.
- **Pré-requis** : la couche doit être **activée dans le panneau gauche**
  (un message le rappelle sinon).

## 2. Comparaison d'état

- **But** : répartition des ouvrages par état général (`Etat<X>.etat_general`).
- **Module** : fenêtre flottante `#dg-window` (barres colorées du mauvais au bon).
- **Données** : `GET api/ouvrages/etat-comparaison/?couche=`.

## 3. Débit mobilisé (carte)

- **But** : cercles proportionnels au débit de l'ouvrage.
- **Module** : carte, **slot `resultat`**.
- **Champ débit par couche** : seuils → `debit_mobilise` ; barrages / prises →
  `debit_derive` ; khettaras / forages / tronçons → `debit`.
- **Données** : `GET api/ouvrages/debit-points/?couche=` (point_on_surface pour
  les tronçons, point direct pour les ouvrages ponctuels).

## 4. Assolement

- **But** : répartition des surfaces par culture d'un périmètre.
- **Module** : fenêtre flottante (camembert / donut).
- **Sélection** : périmètre (menu).
- **Données** : ♻ `GET api/perimetre/<pk>/rendement/` (assolement + culture
  dominante + rendement pondéré).

---

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| [carte/api_views.py](api_views.py) | `ouvrages_etat_comparaison`, `ouvrages_debit_points` (+ réutilise `indice_priorite`, `outil_scoring`, `criteres_scoring`, `perimetre_rendement`). |
| [carte/urls.py](urls.py) | Routes `api/ouvrages/etat-comparaison/`, `api/ouvrages/debit-points/`. |
| [carte/static/carte/js/outils-diagnostic.js](static/carte/js/outils-diagnostic.js) | Contrôleur (fenêtre `#dg-window`). |
| `templates/carte/index.html` | Box, 4 sous-panneaux, fenêtre `#dg-window`. |

## Capture Layout / PDF

Les cercles « Débit mobilisé » sont recomposés via `CarteRendu.getOverlay()`.
La recoloration Indice/Scoring (WebGL) est capturée nativement. Les fenêtres
(Comparaison d'état, Assolement) sont hors carte.

> Note : l'ancien Indice de priorité de `panneau-droit.js` (non chargé) appliquait
> `fill-color` — inadapté aux couches points/lignes. La version de cette box cible
> la propriété correcte selon la géométrie.
