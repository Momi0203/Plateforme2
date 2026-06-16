# Box « Hydrologie / Crues » — panneau droit Outils de la Carte

Documentation des outils de la box **Hydrologie / Crues** (`/carte/`, panneau
droit **Outils**). Tous réutilisent les fonctions de l'app `analyse_hydrologique`
et passent par le gestionnaire de rendu **`CarteRendu`** (carte) ou par
**`window.FloatingChart`** (fenêtres graphiques multi-instances —
`static/carte/js/outils-commun.js`).

> **Évolutions Lots A–F** : les fenêtres graphiques sont désormais
> **multi-instances** (chaque exécution ouvre une nouvelle fenêtre, cascade,
> illimitée — point 3). La couche `bv_ouvrage_tete` (masquée) est **activable**
> via la box **Couches** (voir [OUTILS_COUCHES.md](OUTILS_COUCHES.md)). L'ancien
> outil « Bassins versants & réseau » a été **retiré** (remplacé par
> « Hydrologie 2 » + « Réseau du BV »).

> **Sélection** : les outils sur BV (Débits de crue, Tc, Apports) utilisent
> encore un **menu déroulant** `bv_ouvrage_tete` (couche masquée) ; les outils
> d'apport par ouvrage utilisent la **sélection carte** (point 1).

---

## 1. Débits de crue (T)

- **But** : barres Q10 / Q20 / Q50 / Q100 d'un bassin versant.
- **Module** : fenêtre flottante (`FloatingChart`, Chart.js).
- **Données** : `GET api/bv/<pk>/crue-periodes/` — **lecture** de la dernière
  `ResultatAnalyseHydrologique` (aucun recalcul).

## 2. Temps de concentration

- **But** : Tc par formule (Kirpich, Turraza…) + moyenne.
- **Module** : fenêtre flottante.
- **Données** : `GET api/bv/<pk>/tc/` → **calcul** via `bv_to_hydro` +
  `hydrologie_bv.calculer_tc_bv` (toutes les `FORMULES_TC_DISPONIBLES`).

## 3. Apports de crue mensuels

- **But** : volumes de crue mensuels (12 mois Sep→Aoû) × 3 années, pour le BV cible.
- **Module** : fenêtre flottante (barres groupées normale / humide / sèche).
- **Sélection** : BV cible (menu) + station hydrométrique (menu) + Tc optionnel.
- **Données** : `GET api/bv/<pk>/apports-crue/?station=<pk>&tc=<h>` →
  `calculer_apports_crue_sans_prelevement`. **`station` et `tc` sont désormais
  optionnels** (station auto = la plus proche/dans le BV ; Tc auto) — cf.
  helper `_compute_apports_crue` (Lot F).
- **Transposition Francou-Rodier** : Qp de la station (BV jaugé) transposés vers
  le BV cible avant l'intégration de l'hydrogramme de Nash.

## 4. Crue de projet (carte) — *modes (Lot D)*

- **But** : thématique du débit de pointe Q(T) par bassin.
- **Module** : carte, **slot `resultat`** (`CarteRendu`).
- **Modes de présentation** (point 4) : **cercles proportionnels** (défaut),
  cercles classés (quantiles) — via `RenduCarte.renderThematique`.
- **Données** : `GET api/bv/crue-points/?t=<10|20|50|100>&pks=` — point_on_surface
  du BV + Q(T) de la dernière analyse.

## 5. Apport de crue — seuil / prise / barrage — *nouveau (Lot F)*

- **But** : pour un ouvrage, **apport de crue du BV** (transposé, 12 mois × 3
  années) **+ volume capté** au droit de l'ouvrage (Q6 = les deux).
- **Module** : fenêtre flottante (`FloatingChart`).
- **Sélection carte** (point 1) : 1ʳᵉ entité sélectionnée sur `seuils` /
  `prises_locales` / `barrages`.
- **Données** : `GET api/seuil|prise|barrage/<pk>/apport-crue/` →
  `_compute_apports_crue(bv)` + volume capté = `debit × 31 536` (m³/an)
  (`debit_mobilise` pour le seuil, `debit_derive` pour prise/barrage).
- **Repli** : si l'ouvrage n'a pas de `bassin_versant` lié, la fenêtre affiche
  le **volume capté** seul + un message (pas de graphe d'apport).

---

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| [carte/api_views.py](api_views.py) | `bv_crue_periodes`, `bv_tc`, `bv_apports_crue`, `_compute_apports_crue`, `bv_crue_points`, `seuil/prise/barrage_apport_crue`. |
| [carte/urls.py](urls.py) | Routes `api/bv/*`, `api/<ouvrage>/<pk>/apport-crue/`. |
| [carte/static/carte/js/outils-hydrologie.js](static/carte/js/outils-hydrologie.js) | Contrôleur de la box (FloatingChart + apport ouvrage). |
| `templates/carte/index.html` | Box, sous-panneaux (crue, tc, apports, crue projet, 3 apports ouvrage). |

## Capture Layout / PDF

Les cercles (Crue de projet) sont des marqueurs DOM → recomposés par `layout.js`
via `CarteRendu.getOverlay()`. Les fenêtres `FloatingChart` (graphes) sont hors
capture carte. Le réseau « ouvrage de tête » (box Couches) est une couche WebGL
capturée nativement.
