# Plan de mise à jour — Panneau droit « Outils » de la Carte

> Fait suite à [PLAN_EXECUTION_OUTILS_CARTE.md](PLAN_EXECUTION_OUTILS_CARTE.md)
> (lots 0→5 livrés : 5 boxes, 16 outils, `CarteRendu`, couche masquée
> `bv_ouvrage_tete`). Ce document décrit **6 évolutions** demandées sur les outils
> existants + les nouveaux outils.
>
> **Statut : LOTS A–G LIVRÉS** (voir §8 et le détail ci-dessous). Reste à
> valider en navigateur + import des 3 shapefiles réseau (Guir/Rhéris/Maïder).

---

## ✅ Statut d'exécution (Lots A–G)

| Lot | Contenu | État |
|---|---|---|
| **A** | Socle : `outils-commun.js` (`OutilsSel`, `FloatingChart`, `OutilsChart`) + `outils-rendu.js` (`RenduCarte`) | ✅ |
| **B** | Point 1 — sélection carte : Diagnostic (scoring couche+carte, comparaison d'état, débit mobilisé, assolement), Bilan (bilan mensuel, ET0). Hydrologie/Efficience différés (couche masquée / backend) | ✅ |
| **C** | Points 2 & 3 — `FloatingChart` multi-fenêtres sur tous les outils B ; multi-entités ET0 (fan-out), Comparaison besoin/d'état déjà multi | ✅ |
| **D** | Point 4 — modes Module A : Crue de projet, Taux de couverture, Débit mobilisé, Rendement tronçons (`RenduCarte.renderThematique`) | ✅ |
| **E** | Point 5 — box « Couches » / Hydrologie 2 : 5 couches réseau + `bv_ouvrage_tete` activables ; « Réseau du BV » (forcé, clip BV) ; retrait de l'ancien outil BV & réseau | ✅ |
| **F** | Point 6 — apport crue : station/Tc auto ; apport seuil/prise/barrage (apport BV transposé + volume capté) ; 3 outils dans la box Hydrologie | ✅ |
| **G** | Docs (`OUTILS_*.md` + `OUTILS_COUCHES.md`), capture Layout/PDF vérifiée, statut | ✅ |

**Reste à faire (hors code)** : test navigateur de bout en bout ; import des
shapefiles Guir/Rhéris/Maïder ; renseigner le FK `bassin_versant` + les débits
des ouvrages pour que les apports seuil/prise/barrage produisent des graphes.

---

## 0. Rappel de l'existant (ancrage code)

| Brique | Fichier | Rôle |
|---|---|---|
| Sélection carte | [static/carte/js/selection.js](static/carte/js/selection.js) | `window.selection_par_couche = { couche: [pks] }`, `selection_active`, `SELECTION_SCOPE`, `applySelectionFromPks()`, évènement `carte:selectionChange` |
| Gestionnaire de rendu | [static/carte/js/carte-rendu.js](static/carte/js/carte-rendu.js) | slots `contexte` / `resultat`, légende unifiée, `getOverlay()` |
| Module A (carte) | [static/carte/js/outils-perimetre.js](static/carte/js/outils-perimetre.js) | patron **Besoin** : sélection carte + **5 modes** (`point_valeur`, `cercle_prop`, `camembert`, `barres`, `choroplethe`) |
| Module B (fenêtre) | idem (`#cb-window`) + [outils-hydrologie.js](static/carte/js/outils-hydrologie.js) (`#hy-window`) | patron **Comparaison besoin** : fenêtre flottante Chart.js, **plafond 25** |
| Outils par box | `outils-hydrologie.js`, `outils-bilan.js`, `outils-efficience.js`, `outils-diagnostic.js` | une box = un fichier |
| Registre couches | [layers.py](layers.py) | `LAYER_REGISTRY` (15 visibles + `bv_ouvrage_tete` masquée) |
| Panneau gauche (ligne couche) | [static/carte/js/map.js](static/carte/js/map.js) `_renderListeCouches` | boutons par couche : symbologie, **requête**, **multicritère** (`couche-multi-btn`), sélection, centrer, isoler |
| Endpoints | [api_views.py](api_views.py) + [urls.py](urls.py) | `couche/<nom>/`, `…/liste/`, `…/extent/`, apports crue, etc. |
| Panneau droit (markup) | [templates/carte/index.html](../templates/carte/index.html) | `#po-outils-liste` → boxes `.po-group` ; sous-panneaux `.po-panel-*` ; fenêtres `#hy-window`/`#cb-window`/… |

**Constat clé** : aujourd'hui la plupart des outils (sauf Besoin/Comparaison)
sélectionnent leur entité via un **menu déroulant** (`_fillSelect` →
`/carte/api/couche/<couche>/liste/`) et **une seule entité** à la fois. Les
fenêtres réutilisent un **conteneur unique** (`#hy-window`) → la 2ᵉ exécution
écrase la 1ʳᵉ. Les outils carte (sauf Besoin) ont un **rendu figé** (pas de choix
de mode). C'est exactement ce que les 6 points corrigent.

---

## 1. ⭐ Point 1 — Supprimer la sélection manuelle, sélectionner sur la carte

**Objectif** : aligner **tous** les outils sur le patron **Besoin** : la
sélection se fait **sur la carte** (clic / rectangle / requête, déjà gérés par
`selection.js`), plus de menu déroulant. « Sélection vide = toute la couche ».

### 1.1 Helper de sélection unifié (nouveau)

Nouveau module léger **`static/carte/js/outils-commun.js`** (chargé avant les
`outils-*.js`) :

```js
window.OutilsSel = {
  pks(couche)  {                         // PKs sélectionnés sur cette couche
    const p = window.selection_par_couche || {};
    return (p[couche] || []).map(Number);
  },
  count(couche){ return this.pks(couche).length; },
  // Branche un input lecture seule + le maintient à jour sur carte:selectionChange
  bindCount(inputId, couche, { plafond } = {}) { … }
};
```

### 1.2 Remplacement par outil

| Outil | Avant (déroulant) | Après (sélection carte sur la couche) |
|---|---|---|
| Débits de crue, Tc | `hy-crue-bv`, `hy-tc-bv` (1 BV) | sélection sur **`bv_ouvrage_tete`** |
| Apports de crue | `hy-apports-bv` + `hy-apports-station` | sélection sur `bv_ouvrage_tete` (station auto, cf. §6) |
| Bilan mensuel | `bl-bilan-*` (1 périmètre) | sélection sur `perimetres` |
| ET0 climatique | `eto` (1 station) | sélection sur `stations_clim` |
| Efficience ouvrage de tête | liste `Efficience` | sélection sur la couche d'ouvrage de tête |
| Comparaison d'état, Débit mobilisé | `dg-etat-couche`, `dg-debit-couche` | sélection sur la couche d'ouvrage |
| Apport seuil / prise (§6) | — | sélection sur `seuils` / `prises_locales` |

Chaque sous-panneau perd son `<select>` et gagne le bloc **Besoin** :
un input `… count` (lecture seule, `OutilsSel.bindCount`) + l'aide
« *Sélectionnez des entités sur la carte ; vide = toute la couche* ».

> Pour les couches **masquées** (`bv_ouvrage_tete`, 5 réseaux), elles doivent
> d'abord être activées via la **box « Couches »** (§5) pour être sélectionnables
> sur la carte. Garde-fou : si la couche n'est pas chargée, message
> « *Activez la couche … (box Couches) puis sélectionnez sur la carte* ».

### 1.3 ⚠ Cas extrême — Indice de priorité / Scoring

Le scoring garde le **choix du type d'ouvrage** (`dg-prio-couche`) — il en a
besoin pour charger les **critères** (`/carte/api/couche/<couche>/criteres/`) —
**et ajoute** la sélection carte : si des entités de cette couche sont
sélectionnées, le scoring ne porte que sur elles (`pks` envoyés à
`/carte/api/outils/scoring/` & `…/indice-priorite/`), sinon sur toute la couche.
→ **les deux mécanismes coexistent** (couche + sélection carte).

**Fichiers** : `outils-commun.js` (nouveau), tous les `outils-*.js`,
`index.html` (sous-panneaux), `api_views.py` (scoring/indice acceptent `pks`).

---

## 2. ⭐ Point 2 — Outils Module B : plusieurs entités, un seul graphe

**Objectif** : chaque outil « fenêtre » (Module B) accepte **plusieurs entités**
d'une couche et les **superpose dans le même graphique** (séries multiples /
barres groupées).

- **Plafond par outil** : chaque outil définit son `MAX`, avec **`MAX ≥ 12`**.
  ✅ **Décision Q1** : plafond **plus élevé (25)** pour les outils à
  représentation **agrégée/barres** (peu encombrants) ; **12** pour les outils à
  **courbes 12 mois** (au-delà le graphe devient illisible). Au-delà du plafond →
  troncature aux `MAX` premiers + badge d'avertissement (mécanique
  `tronque`/`total` déjà présente dans Comparaison besoin).
- **Endpoints** : passer de `…/<pk>/…` à un paramètre **`?pks=`** (liste) et
  renvoyer `{ count, total, tronque, items:[ {pk, nom, …} ] }`.

| Outil | Représentation multi-entités | `MAX` |
|---|---|---|
| Débits de crue (B1) | barres groupées T10/T20/T50/T100, 1 couleur par BV | **25** |
| Temps de concentration (B2) | barres : Tc moyen par BV (détail par formule en infobulle) | **25** |
| Apports de crue (B3) | 1 courbe (12 mois) par BV, année choisie | **12** |
| Bilan mensuel (C1) | besoins/ressources — 1 paire de courbes par périmètre (ou facettes) | **12** |
| ET0 climatique (C3) | 1 courbe (12 mois) par station | **12** |
| Efficience ouvrage de tête (D1) | barres globale P/S/T groupées par ouvrage | **25** |
| Comparaison d'état (A2→B) | barres empilées par classe d'état | **25** |
| Apport seuil / prise (§6) | apport BV + part captée, 1 série par ouvrage | **12** |
| Profil de pertes séguia (D2) | reste mono-séguia (profil amont→aval) | 1 |

**Fichiers** : tous les `outils-*.js`, `api_views.py` (endpoints `?pks=`),
`urls.py` inchangé (mêmes routes, signature query-string).

---

## 3. ⭐ Point 3 — 2ᵉ lancement = nouveau graphe (ne pas écraser le 1ᵉʳ)

**Objectif** : relancer un outil Module B ouvre une **nouvelle fenêtre**, la
précédente reste affichée (comparaison côte à côte).

### Gestionnaire multi-fenêtres (nouveau) — `window.FloatingChart`

Dans `outils-commun.js` : remplace les conteneurs uniques `#hy-window` /
`#bl-window` / `#ef-window` / `#dg-window` par une **fabrique** :

```js
FloatingChart.open({ titre, sousTitre }) -> { setStatus, drawChart(config,minW), close }
```

- Clone un gabarit `<div class="fc-window">` (drag sur l'en-tête, croix de
  fermeture, `z-index` croissant), **décalage en cascade** (+24 px) à chaque
  ouverture, **id unique**, **instance Chart.js propre**.
- ✅ **Décision Q2** : nombre de fenêtres **illimité** (cascade) ; aucun appel
  n'écrase l'autre, pas de recyclage automatique.
- Bouton global **« Fermer toutes les fenêtres »** dans l'en-tête du panneau
  droit (seul moyen de nettoyage groupé puisque illimité).

> Les fenêtres existantes (`_hyChart`, `#hy-window`, etc.) sont **refactorées**
> vers `FloatingChart` : un seul moteur de fenêtre pour toutes les boxes.
> Le markup `#hy-window`/`#cb-window`/… est remplacé par un **gabarit unique**
> `#fc-window-template` + un conteneur `#fc-stack`.

**Note Module A (carte)** : le point 3 ne concerne **que les graphes** (Module
B). Sur la carte, la règle anti-désordre de `CarteRendu` (un seul rendu
`resultat` actif) **reste** — sinon les marqueurs/recolorations se chevauchent.
(Voir ⚠ Q3 si on veut aussi des résultats carte multiples nommés.)

**Fichiers** : `outils-commun.js` (FloatingChart), `index.html` (gabarit +
conteneur, suppression des fenêtres dédiées), tous les `outils-*.js`.

---

## 4. ⭐ Point 4 — Outils Module A : choix du mode de présentation

**Objectif** : chaque outil « carte » (Module A) propose un **sélecteur de
mode**, comme Besoin (qui en a déjà 5).

### 4.1 Mutualiser les primitives de rendu (nouveau)

Extraire de `outils-perimetre.js` les primitives réutilisables vers
**`static/carte/js/outils-rendu.js`** (`window.RenduCarte`) :
`circleEl`, `pieEl`, `barsEl`, `labelEl`, `quantileBreaks`, `classIndex`,
`classStyle`, `propSize`, légendes (`legendClasses`, `legendProp`, `legendYears`).
Besoin et tous les outils A consomment ce module (fin de la duplication).

### 4.2 Modes par outil A

| Outil A | Modes proposés (défaut en gras) |
|---|---|
| Besoin *(existant)* | **point_valeur**, cercle_prop, camembert, barres, choroplethe |
| Crue de projet (B4) | **cercle_prop**, point_valeur, choroplethe (aplat sur le polygone BV) |
| Taux de couverture (C2) | **choroplethe**, point_valeur, cercle_prop |
| Débit mobilisé (A3) | **cercle_prop**, point_valeur |
| Rendement tronçons (D3) | **choroplethe (lignes)**, classes (épaisseur) |

Tous passent par `CarteRendu.set('resultat', …)` (markers / choro / overlay /
légende) → capture PDF et effacement déjà gérés.

**Fichiers** : `outils-rendu.js` (nouveau), `outils-perimetre.js` (consomme le
module), `outils-hydrologie.js` / `outils-bilan.js` / `outils-efficience.js` /
`outils-diagnostic.js` (ajout du `<select>` mode + branchement), `index.html`
(ajout du `<select>` dans les sous-panneaux A).

---

## 5. ⭐ Point 5 — Box « Couches » + groupe « Réseaux ouvrage de tête »

**Objectif** : supprimer l'outil **« Bassins versants & réseau »** (Hydrologie)
et le remplacer par une **box « Couches »** dont l'outil **« Hydrologie 2 »**
active, dans le **panneau gauche**, un **nouveau groupe de 6 couches** que
l'utilisateur affiche/masque à volonté.

### 5.1 Les 6 couches

| Clé registre | Modèle | Géom | Label |
|---|---|---|---|
| `bv_ouvrage_tete` *(existe, masquée)* | `analyse_hydrologique.BassinVersant` | Polygon | Bassins versants (ouvrage de tête) |
| `reseau_tete_ziz` | `carte.ReseauOuvrageTeteZiz` | LineString | Réseau ouvrage de tête — Ziz |
| `reseau_tete_moulouya` | `carte.ReseauOuvrageTeteMoulouya` | LineString | … Moulouya |
| `reseau_tete_guir` | `carte.ReseauOuvrageTeteGuir` | LineString | … Guir |
| `reseau_tete_rheris` | `carte.ReseauOuvrageTeteRheris` | LineString | … Rhéris |
| `reseau_tete_maider` | `carte.ReseauOuvrageTeteMaider` | LineString | … Maïder |

→ Entrées à ajouter dans [layers.py](layers.py) avec `"hidden": True` **et** un
flag de groupe activable `"groupe_activable": "Réseaux ouvrage de tête"`
(les 5 réseaux + `bv_ouvrage_tete`). Champs réseau : `["grid_code"]`.
*(Ziz / Moulouya sont déjà peuplés ; Guir/Rhéris/Maïder à importer si besoin via
`import_reseau_<bassin>`.)*

### 5.2 Activation côté panneau gauche

- Nouvel endpoint **`GET /carte/api/couches/activables/`** → métadonnées des 6
  couches `groupe_activable` (le filtre `hidden` de `liste_couches` reste
  inchangé pour la liste principale).
- L'outil « Hydrologie 2 » (toggle) appelle cet endpoint puis demande à `map.js`
  d'**injecter un `<details>` « Réseaux ouvrage de tête »** dans `#couches-liste`,
  avec le **même gabarit de ligne** que les autres couches (donc **symbologie,
  requête, sélection, centrer, isoler fonctionnent à l'identique** — ils ne
  dépendent que de l'appartenance à `LAYER_REGISTRY`). Désactivation → retrait du
  groupe et des couches chargées.
- Petit refactor de `_renderListeCouches` : extraire le gabarit de ligne en
  fonction `_coucheRowHtml(c)` réutilisée pour l'injection dynamique.

### 5.3 ✅ Spécificité des 5 réseaux : appariement BV → réseau (logique `analyse_hydrologique`)

> **Décision Q5** (réponse utilisateur) : ce **n'est pas** une intersection
> générique « tronçon réseau ↔ polygone BV ». C'est la **reprise de la logique de
> présentation des réseaux de l'app `analyse_hydrologique`** — l'appariement
> automatique entre un **bassin versant (couche `bv_ouvrage_tete`)** et **le bon
> réseau parmi les 5** couches d'ouvrage de tête.

Logique de référence à porter (déjà implémentée dans
[analyse_hydrologique/views.py](../analyse_hydrologique/views.py)) :

- **`_reseau_ouvrage_tete_pour_bv(bv, min_grid_code=None)`** :
  1. surface d'intersection (EPSG:26191, m²) entre `bv.geometrie` et chaque
     `carte.BassinVersant` → retient le bassin le **plus recouvrant** ;
  2. mappe ce bassin vers son modèle `ReseauOuvrageTete<X>`
     (`_RESEAU_OT_PAR_BASSIN`) ;
  3. renvoie les tronçons du réseau **intersectant** le BV, avec **filtrage
     adaptatif du grid_code** (`RESEAU_SEUIL_INTERSECTION_M2 = 500 km²` : petite
     intersection → réseau complet, grid faible inclus ; grande → drains forts
     `grid_code ≥ 1` avec repli).
- **`bv_reseau_geojson`** : FeatureCollection `{grid_code, geometry}` (override
  `?min_grid_code=`).
- **Symbologie** : `analyse_hydrologique/.../reseau_personnalisable.js`
  (`ReseauPersonnalisable`) — classes log(grid_code), couleur / épaisseurs /
  nombre de classes réglables, sélecteur « détail réseau ».

Pour les **5 couches réseau** (pas pour `bv_ouvrage_tete`), le bouton
**multicritère** (`couche-multi-btn`) est **remplacé** par un bouton
**« Réseau du BV »** (`couche-inter-btn`, icône `fa-water` / `fa-diagram-project`).
Il ouvre un mini-panneau (mécanique `pg-tab-*`) : l'utilisateur **sélectionne un
BV sur la carte** (couche `bv_ouvrage_tete`), et l'outil affiche **la couche
réseau cliquée**, **clippée au BV**, avec le filtrage grid_code adaptatif et la
symbologie graduée.

> ✅ **Décision Q5-bis** : **mode forcé** — on **respecte la couche réseau
> cliquée** (Ziz, Moulouya, …) et on se contente de la **clipper au BV
> sélectionné**. **Pas** d'appariement automatique des 5 bassins (on n'exécute
> donc PAS l'étape 1 de `_reseau_ouvrage_tete_pour_bv`, le calcul de la plus
> grande intersection). On ne reprend que **l'étape 3** : filtre
> `geometrie__bboverlaps + intersects` du BV + filtrage grid_code adaptatif
> (`RESEAU_SEUIL_INTERSECTION_M2`). ⚠ Conséquence à signaler à l'utilisateur :
> si la couche réseau cliquée ne couvre pas le BV sélectionné, le résultat sera
> vide (c'est volontaire — le choix de la couche lui appartient).

- Nouvel endpoint **`GET /carte/api/reseau-ouvrage-tete/?reseau=<couche>&bv=<pk>&min_grid_code=`**
  qui prend **la couche réseau choisie** + le BV sélectionné → renvoie le GeoJSON
  (tronçons de cette couche intersectant le BV + grid_code) + métadonnées
  (`reseau_count`, `reseau_longueur_km`, `reseau_grid_max`). On réutilise la
  logique de clip + grid_code de `_reseau_ouvrage_tete_pour_bv` (étape 3
  uniquement) ; on peut factoriser cette partie dans un helper partagé.
- Rendu : couche WebGL graduée par `grid_code` (transposition du
  `ReseauPersonnalisable` Leaflet → MapLibre), via `CarteRendu` slot `contexte`.

**Fichiers** : `layers.py` (+5 entrées + flag), `api_views.py`
(`couches_activables`, `reseau_ouvrage_tete`), `urls.py` (+2 routes),
`map.js` (gabarit de ligne + injection dynamique + bouton « Réseau du BV »),
`index.html` (box « Couches » + mini-panneau), nouveau `outils-couches.js`
(+ portage symbologie graduée grid_code). **Suppression** : item `hy-viz` +
`hy-panel-viz` (markup) + fonctions `_vizAfficher/_installViz/_removeViz/_vizClear`
de `outils-hydrologie.js`. **Mutualisation possible** : déplacer
`_reseau_ouvrage_tete_pour_bv` + constantes dans un module importable par les
deux apps (éviter un import croisé `carte → analyse_hydrologique.views`).

---

## 6. ⭐ Point 6 — Logique d'apport de crue + apport seuil & prises

**Objectif** : actualiser le calcul d'apport de crue et **ajouter l'apport pour
les seuils et les prises** (aujourd'hui seul le **barrage** renvoie des apports
mensuels via `BilanOuvrageAssocie` ; seuil/prise ne renvoient que les paramètres
du BV — cf. `_bv_apport_data`, `seuil_bv_apport`, `prise_bv_apport` dans
[api_views.py](api_views.py)).

### 6.1 Actualisation du moteur (existant `bv_apports_crue`)

- **Sélection auto de la station** : aujourd'hui `?station=` est obligatoire.
  Choisir automatiquement la station hydrométrique de référence (station du BV /
  la plus proche) ; `?station=` ne reste qu'un *override*.
- **Tc auto** : calculé via `calculer_tc_bv` (B2) si non fourni.
- **Transposition Francou-Rodier** déjà gérée (`transposition`) — conservée et
  documentée dans la réponse.

### 6.2 Apport seuil & prise (nouveau)

- `GET /carte/api/seuil/<pk>/apport-crue/` et `…/prise/<pk>/apport-crue/` :
  apports **mensuels** (12 mois Sep→Aoû × 3 années) calculés sur le **BV de
  l'ouvrage** (réutilise `calculer_apports_crue_sans_prelevement`), homogènes
  avec l'apport barrage.
- ✅ **Décision Q6** : **les deux** — l'endpoint renvoie (a) l'**apport de crue
  brut du BV** (transposé, 12 mois × 3 années) **et** (b) le **volume
  dérivé/mobilisé** au droit de l'ouvrage (à partir de `debit_mobilise` pour le
  seuil, `debit_derive` pour la prise). La présentation montre l'apport BV et la
  **part captée** par l'ouvrage côte à côte.
- Exposition : (i) dans les **panneaux de drill-down** existants (clic droit →
  ouvrage, déjà consommateurs de `*_bv_apport`) **et** (ii) en **outils
  Module B** « Apport de crue » du panneau droit (sélection carte multi-entités,
  §1+§2), une fenêtre par ouvrage/sélection.

**Fichiers** : `api_views.py` (refactor `bv_apports_crue` + 2 endpoints),
`urls.py` (+2 routes), `outils-hydrologie.js` (outils Apport seuil/prise),
`drilldown.js` (affichage apport seuil/prise), `index.html` (sous-panneaux).

---

## 7. Organisation cible du panneau droit

| Box | Outils (modif) | Module |
|---|---|---|
| **Couches** *(nouvelle)* | Hydrologie 2 — active les 6 couches ouvrage de tête (§5) | — |
| **Outils périmètre** | Besoin (A, modes ✔), Comparaison besoin (B, multi ✔) | A / B |
| **Hydrologie / Crues** | Débits de crue (B multi), Temps de concentration (B multi), Apports de crue (B multi), **Crue de projet (A + modes)**, **Apport seuil (B)**, **Apport prise (B)**, **Apport barrage (B)** (§6) — *retrait de « Bassins versants & réseau »* | A / B |
| **Bilan eau** | Bilan mensuel (B multi), **Taux de couverture (A + modes)**, ET0 climatique (B multi) | A / B |
| **Efficience réseau** | Efficience ouvrage de tête (B multi), Profil de pertes (B mono), **Rendement tronçons (A + modes)** | A / B |
| **Diagnostic** | Indice de priorité / Scoring (A + modes, **couche + sélection carte**), Comparaison d'état (B multi), **Débit mobilisé (A + modes)**, Assolement (B) | A / B |

---

## 8. Lots d'exécution (ordre recommandé)

> Après chaque lot : `manage.py check`, compilation des templates, smoke test des
> endpoints (pas de runtime JS dans l'env de dev — test navigateur en fin).

- **Lot A — Socle transversal** : `outils-commun.js` (`OutilsSel`,
  `FloatingChart`) + `outils-rendu.js` (primitives Module A) ; branchement
  `index.html`. *(prérequis des points 1-2-3-4)*
- **Lot B — Point 1** : retrait des déroulants → sélection carte sur tous les
  outils ; cas scoring (couche + carte).
- **Lot C — Points 2 & 3** : endpoints `?pks=` multi-entités + refonte des
  fenêtres vers `FloatingChart` (multi-fenêtres).
- **Lot D — Point 4** : sélecteur de mode sur les 4 outils A restants (Crue de
  projet, Taux de couverture, Débit mobilisé, Rendement tronçons).
- **Lot E — Point 5** : box « Couches » + 5 entrées réseau + injection groupe
  panneau gauche + intersection réseau↔BV ; suppression de l'outil BV & réseau.
- **Lot F — Point 6** : refonte apport crue + apport seuil/prise + exposition
  drill-down et outils.
- **Lot G — Docs & finitions** : MAJ `OUTILS_*.md`, vérif capture PDF
  (`CarteRendu.getOverlay()` + `FloatingChart`), harmonisation libellés FR.

---

## 9. Questions — décisions & reste à valider

**Décidé :**
- ✅ **Q1 — Plafond multi-entités** : **25** pour les outils agrégés/barres,
  **12** pour les courbes 12 mois (cf. tableau §2).
- ✅ **Q2 — Multi-fenêtres** : **illimité** (cascade) + bouton « Fermer toutes ».
- ✅ **Q3 — Anti-désordre carte** : on **garde « un seul résultat carte actif »**
  (`CarteRendu` slot `resultat`). Le multi-instances du point 3 ne concerne que
  les **graphes Module B** (`FloatingChart`).
- ✅ **Q4 — Apport seuil/prise/barrage** : rangés **dans la box Hydrologie /
  Crues** (pas de box dédiée).
- ✅ **Q5 — Réseau des 5 couches** : **reprise de la logique
  `analyse_hydrologique`** (`_reseau_ouvrage_tete_pour_bv` / `bv_reseau_geojson` /
  `ReseauPersonnalisable`) — appariement BV → réseau, **pas** une intersection
  générique tronçon↔polygone (cf. §5.3).
- ✅ **Q6 — Apport seuil/prise** : **les deux** — apport de crue brut du BV
  (transposé) **+** volume dérivé/mobilisé au droit de l'ouvrage (cf. §6.2).

- ✅ **Q5-bis — Appariement réseau** : **forcé** (couche réseau cliquée + clip
  au BV, sans appariement auto des 5 bassins — cf. §5.3).
- ✅ **Q7 — Réseaux manquants** : **importer maintenant** Guir / Rhéris / Maïder.
  ⚠ **Bloqué** : les 5 modèles existent, **Ziz (152 671) et Moulouya (82 038)
  sont peuplés**, mais **Guir / Rhéris / Maïder = 0** et le dossier
  `plateformeSIG/static/resaux hydrographique ouvrage en tete/` **n'existe pas**.
  → **Prérequis** : déposer `guir.shp`, `rheris.shp`, `maider.shp` (+ `.shx`,
  `.dbf`, `.prj`) dans ce dossier, puis lancer
  `python manage.py import_reseau_guir/_rheris/_maider`. Les 5 entrées du registre
  sont créées dès le Lot E ; les 3 couches vides resteront simplement sans
  données jusqu'à l'import.

> **Toutes les questions sont tranchées.** Le seul point bloquant est la
> **fourniture des 3 shapefiles** (Q7). Je peux démarrer le **Lot A** (socle
> transversal) immédiatement, puis l'ordre B→G ; le Lot E reste codable, l'import
> des 3 réseaux se fera dès réception des fichiers.
