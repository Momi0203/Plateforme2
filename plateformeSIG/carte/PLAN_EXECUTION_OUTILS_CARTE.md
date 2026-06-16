# Plan d'exécution — Boxes & Outils de la Carte

> Fait suite à [PROPOSITION_OUTILS_CARTE.md](PROPOSITION_OUTILS_CARTE.md) et
> intègre les retours : couche des BV d'ouvrage de tête, outil de visualisation
> BV + réseau (2 symbologies), place des outils **Indice de priorité** &
> **Scoring**, et **affichage des résultats sur la carte sans désordre**.
>
> **Statut : à valider avant exécution.**

---

## 0. Réponses aux points soulevés

### 0.1 « La box Hydrologie / Crues s'applique à quelle couche ? »

Aux **bassins versants de l'app `analyse_hydrologique`** (`analyse_hydrologique.BassinVersant`)
— ce sont eux qui portent les analyses de crue, le Tc et le lien aux ouvrages de
tête. Or **cette couche n'existe pas** dans le module Carte : seul
`carte.BassinVersant` (un modèle **distinct**, sans analyses) est exposé.

➡ **Action** : ajouter `analyse_hydrologique.BassinVersant` au registre des
couches **mais masquée du panneau gauche** (voir §1). Les outils Hydrologie la
sélectionnent via une **liste déroulante** (pas de toggle dans le panneau gauche).

### 0.2 « Visualiser les BV avec le réseau hydrographique → un outil à 2 symbologies »

Créer l'outil **« Bassins versants & réseau »** (box Hydrologie). Il superpose,
à la demande, les **BV (analyse_hydrologique)** + le **réseau hydrographique**,
avec **2 options de symbologie** (voir §3). C'est lui qui rend visible la couche
masquée — pas le panneau gauche.

### 0.3 « Indice de priorité et Scoring sont des outils importants »

Exact, et ils **existent déjà** (`indice_priorite`, `outil_scoring`). Le plan les
**remonte dans la nouvelle box « Diagnostic »** comme outils de premier plan (au
lieu de les laisser noyés dans la symbologie), en plus des outils A1–A3 proposés.

### 0.4 « Présenter des résultats sur la carte sans désordre entre eux » ⭐ (point clé)

C'est le risque majeur quand plusieurs outils « carte » (Module A) dessinent en
même temps (marqueurs qui se superposent, recolorations WebGL concurrentes,
légendes empilées). **Solution** : un **gestionnaire de rendu unique**
(`carte-rendu.js`) qui impose **un seul rendu thématique actif à la fois** et une
**légende unifiée** (voir §2). Les outils « fenêtre » (Module B) restent **hors
carte** → ils ne perturbent jamais l'affichage cartographique.

---

## 1. Couche masquée — BV d'ouvrage de tête

### Mécanisme (déjà supporté par l'architecture)

Le panneau gauche est construit par `map.js` depuis `GET /carte/api/couches/`
(`liste_couches`), qui itère `LAYER_REGISTRY`. Les outils, eux, interrogent
`GET /carte/api/couche/<nom>/…` (`geojson_couche`) qui vérifie seulement
l'appartenance à `LAYER_REGISTRY`.

➡ Il suffit d'un flag **`"hidden": True"`** dans l'entrée du registre, **filtré
dans `liste_couches`** (absent du panneau gauche) mais **toujours servi** par
`geojson_couche` / `extent_couche` (donc utilisable par les outils).

### Entrées à ajouter dans [layers.py](layers.py)

```python
"bv_ouvrage_tete": {
    "model": "analyse_hydrologique.BassinVersant",
    "geom_field": "geometrie", "geom_type": "Polygon",
    "groupe": "Hydrologie", "label": "Bassins versants (ouvrage de tête)",
    "fields": ["nom", "surface", "perimetre", "z_min", "z_max",
               "thalweg", "ouvrage_en_tete"],
    "hidden": True,           # ← absent du panneau gauche
},
# (optionnel) réseau d'ouvrage de tête, si retenu comme source réseau :
# une entrée hidden par bassin (ReseauOuvrageTeteZiz, …Moulouya, …)
```

### Modif minimale de [api_views.py](api_views.py) → `liste_couches`

```python
data = [ {...} for cle, meta in LAYER_REGISTRY.items()
         if not meta.get("hidden") ]
```

> Aucune autre vue ne change : `geojson_couche`, `geojson_entite`,
> `extent_couche`, `valeurs_champ`, `stats_champ` continuent de fonctionner pour
> une couche masquée.

---

## 2. Gestionnaire de rendu carte — anti-désordre ⭐

Nouveau module partagé **`carte-rendu.js`** (`window.CarteRendu`), socle commun à
**tous** les outils Module A (y compris **Besoin** et **Indice de priorité**
existants, qu'on y branche).

### Principes

1. **Un seul rendu « résultat » actif à la fois.** Avant d'installer un nouveau
   rendu, le manager **efface le précédent** (retrait des marqueurs, restauration
   des `fill-color`/`fill-opacity` WebGL sauvegardés). → jamais deux thématiques
   superposées.
2. **Deux emplacements (slots) distincts**, qui peuvent coexister proprement :
   - slot **`contexte`** : la visualisation BV + réseau (§3) ;
   - slot **`resultat`** : la thématique d'un outil (Besoin, Crue, Couverture…).
   Un nouveau rendu n'écrase que **son** slot.
3. **Légende unifiée** : une seule boîte de légende sur la carte (empilable
   contexte + résultat), avec le **nom de l'outil actif** et un bouton
   **« ✕ Effacer »** (par slot) + **« Tout effacer »**.
4. **Règle WebGL** : une seule recoloration (`choroplethe`) par couche de base à
   un instant donné (le manager mémorise/restaure la peinture d'origine).
5. **Capture Layout/PDF** : le manager centralise `getOverlay()` (remplace les
   `window.get<Outil>Overlay()` épars) → l'export reprend le rendu courant.

### API interne (esquisse)

```js
CarteRendu.set(slot, {
  outil, markers, choro:{layer, expr, opacity}, legendeHtml, overlay
});           // efface l'ancien contenu du slot puis installe le nouveau
CarteRendu.clear(slot);     // efface un slot
CarteRendu.clearAll();      // efface tout
CarteRendu.getOverlay();    // pour layout.js (capture PDF)
```

### Refactor d'amorçage

- **Besoin** : remplacer ses `_markers/_overlay/_choroSaved` privés par
  `CarteRendu.set('resultat', …)` / `clear`. (Comportement identique côté
  utilisateur, mais coordonné.)
- **Indice de priorité** : idem (slot `resultat`).
- **Comparaison besoin** : inchangé (Module B, hors carte).

> Résultat : tout outil « carte » futur passe par `CarteRendu` → **pas de
> désordre** possible, légende cohérente, effacement fiable.

---

## 3. Outil « Bassins versants & réseau » (2 symbologies)

- **Box** : Hydrologie. **Slot** : `contexte` (cohabite avec une thématique).
- **Sélection** : liste déroulante (un BV, ou « tous ») depuis `bv_ouvrage_tete`.
- **Source réseau** : à confirmer (§7-Q1) — `carte.ReseauHydrographique`
  (possède `sorder` Strahler) **ou** `ReseauOuvrageTete<Bassin>` (grid_code).
- **2 options de symbologie** :
  - **① Réseau simple** : BV en contour + aplat léger ; réseau en **ligne bleue
    uniforme**. (lecture rapide)
  - **② Réseau hiérarchisé** : réseau **gradué** (épaisseur/couleur par ordre de
    Strahler `sorder` ou `grid_code`) ; BV en **aplat par superficie** (classes).
- **Rendu** : couches WebGL ajoutées/retirées **via `CarteRendu` (slot contexte)**
  → effaçables proprement, n'entrent pas en conflit avec une thématique résultat.
- **Endpoint** : réutilise `GET /carte/api/couche/bv_ouvrage_tete/` +
  `…/couche/<reseau>/` (déjà génériques) ; aucune nouvelle vue serveur requise.
- **Complexité** : ⭐⭐.

---

## 4. Boxes consolidées (avec Indice de priorité & Scoring)

| Box | Outils (★ = existant remonté) | Module |
|---|---|---|
| **Outils périmètre** *(existant)* | Besoin ★, Comparaison besoin ★ | A, B |
| **Diagnostic** | **Indice de priorité ★**, **Scoring ★**, Assolement (A1), Comparaison d'état (A2), Débit mobilisé (A3) | A/B |
| **Hydrologie / Crues** | **Bassins versants & réseau** (§3), Débits de crue (B1), Temps de concentration (B2), Apports de crue mensuels (B3), Crue de projet (B4) | A/B |
| **Bilan eau** | Bilan mensuel (C1), Taux de couverture (C2), ET0 climatique (C3) | A/B |
| **Efficience réseau** | Efficience ouvrage de tête (D1), Profil de pertes séguia (D2), Rendement tronçons (D3) | A/B |

*(Détail des outils A1–D3 : voir la proposition. Inchangé, sauf que tous les
outils Module A passent désormais par `CarteRendu`.)*

---

## 5. Lots d'exécution (ordre recommandé)

> Chaque lot est livrable et testable indépendamment. Après chaque lot :
> `manage.py check`, compilation des templates, smoke test de l'endpoint.

### Lot 0 — Socle (prérequis de tout le reste) — ✅ FAIT
- [x] Flag `"hidden"` + filtrage dans `liste_couches`.
- [x] Entrée `bv_ouvrage_tete` (masquée) dans `LAYER_REGISTRY`.
- [x] **`carte-rendu.js`** (gestionnaire de rendu, slots contexte/résultat,
      légende unifiée) + conteneur `#carte-rendu-legende` + branchement `index.html`.
- [x] Refactor **Besoin** vers `CarteRendu` ; **Indice de priorité** branché de
      façon défensive (panneau-droit.js dormant — non chargé actuellement) ;
      `layout.js` lit `CarteRendu.getOverlay()`.
- **Validé** : `manage.py check` OK ; `liste_couches` masque `bv_ouvrage_tete`
  (15 couches) ; `geojson_couche/bv_ouvrage_tete` → 200 ; template `index` compile.
  *(Test navigateur recommandé : lancer Besoin en 2 modes → un seul rendu actif,
  effacement via la légende carte.)*

### Lot 1 — Box Hydrologie : contexte + crues (cœur de la demande) — ✅ FAIT
> Décisions par défaut : **Q1** réseau = `carte.ReseauHydrographique` (ordre de
> Strahler `sorder`) ; **Q2** sélection par **menu déroulant** (couche BV masquée).
- [x] Outil **Bassins versants & réseau** (2 symbologies, slot contexte +
      cleanup CarteRendu) — `bv_ouvrage_tete` + `reseau_hydrographique`.
- [x] **Débits de crue (B1)** — `GET api/bv/<pk>/crue-periodes/` (fenêtre).
- [x] **Temps de concentration (B2)** — `GET api/bv/<pk>/tc/` → `calculer_tc_bv` (fenêtre).
- [x] **Apports de crue mensuels (B3)** — `GET api/station-hydro/<pk>/apports-crue/`
      → `calculer_apports_crue_sans_prelevement` (fenêtre).
- [x] **Crue de projet (B4)** — `GET api/bv/crue-points/` → cercles proportionnels
      (slot 'resultat' via CarteRendu).
- [x] Endpoint générique **`api/couche/<nom>/liste/`** (menus déroulants).
- **Validé** : `manage.py check` OK ; endpoints testés (146 BV, B1 Q-values, B2
  Tc 8 formules, B3 ~4,3 M m³, B4 3 points) ; template `index` compile.
  *(Test navigateur conseillé : afficher BV+réseau en symbo 2 PUIS Crue de projet
  → les 2 cohabitent — slot contexte + slot résultat — sans désordre.)*

### Lot 2 — Box Bilan eau — ✅ FAIT
- [x] **Bilan mensuel (C1)** — `GET api/perimetre/<pk>/bilan-mensuel/?annee=`
      (lecture dernier `resultats_bilan_*`, fenêtre `#bl-window`).
- [x] **Taux de couverture (C2)** — `GET api/perimetres/couverture/?annee=`
      (cercles classés ress./bes. %, slot 'resultat').
- [x] **ET0 climatique (C3)** — `GET api/station-clim/<pk>/eto/` → `calculer_eto`
      (courbe 12 mois, fenêtre).
- **Validé** : `check` OK ; endpoints testés (C1 AHOULI 121195/206700, C2 170,6 %,
  C3 zaida ET0) ; template `index` compile. Fichiers : `api_views.py` (+3),
  `urls.py` (+3), **`outils-bilan.js`** (nouveau), `index.html` (box + 3 panneaux
  + `#bl-window`).

### Lot 3 — Box Efficience réseau — ✅ FAIT
> Q5 tranchée : **lecture** du dernier `Efficience` stocké (pas de recalcul DB).
- [x] **Efficience ouvrage de tête (D1)** — `GET api/efficiences/liste/`
      (dernier `Efficience` par ouvrage, cascade P/S/T → globale, fenêtre `#ef-window`).
- [x] **Profil de pertes séguia (D2)** — `GET api/seguia/<pk>/profil/` →
      `calculer_efficience_troncon` (propagation amont→aval, persister=False),
      barres empilées débit aval + Pi + Pv (fenêtre).
- [x] **Rendement tronçons (D3)** — couche de lignes colorées par
      `efficience_calculee` (geojson `troncons_seguias`, slot 'resultat' + cleanup).
- **Validé** : `check` OK ; endpoints testés (D1 Seuil#2 globale 60 % / P 73,9 /
  S 81,2 ; D2 SAGUIA AHOULI eff 73,9 %, 3 tronçons propagés) ; template compile.
  Fichiers : `api_views.py` (+3), `urls.py` (+3), **`outils-efficience.js`** (nouveau),
  `index.html` (box + 3 panneaux + `#ef-window`).

### Lot 4 — Box Diagnostic (compléments) — ✅ FAIT
- [x] **Indice de priorité / Scoring** — panneau unifié (couche + critères +
      coefficients + méthode) ♻ `indice-priorite` (seuils fixes) **et** `scoring`
      (quantile / jenks) ; recoloration de `lyr-<couche>` (circle/line selon
      géométrie) via slot 'resultat'.
- [x] **Comparaison d'état (A2)** — `GET api/ouvrages/etat-comparaison/?couche=`
      (barres par état, fenêtre `#dg-window`).
- [x] **Débit mobilisé (A3)** — `GET api/ouvrages/debit-points/?couche=`
      (cercles proportionnels, slot 'resultat').
- [x] **Assolement (A1)** — ♻ `perimetre_rendement` (camembert des surfaces,
      fenêtre).
- **Validé** : `check` OK ; endpoints testés (A2 seuils/troncons/khettaras,
  A3 seuils/troncons) ; template compile. Fichiers : `api_views.py` (+2),
  `urls.py` (+2), **`outils-diagnostic.js`** (nouveau), `index.html` (box + 4
  panneaux + `#dg-window`).

### Lot 5 — Finitions — ✅ FAIT
- [x] **Docs** : un fichier par box (granularité retenue vs 1/outil) —
      `OUTILS_HYDROLOGIE.md`, `OUTILS_BILAN.md`, `OUTILS_EFFICIENCE.md`,
      `OUTILS_DIAGNOSTIC.md` (s'ajoutent à `OUTIL_BESOIN.md` /
      `OUTIL_COMPARAISON_BESOIN.md`).
- [x] **Capture Layout/PDF vérifiée** : les rendus « carte » sont soit des
      marqueurs DOM de type `circle` (recomposés par `layout.js` via
      `CarteRendu.getOverlay()`), soit des couches WebGL (BV+réseau, rendement,
      indice/scoring) capturées **nativement** → aucune modification nécessaire.
- [x] **Harmonisation** : statuts fenêtre `.cb-ok/.cb-err/.cb-muted/.cb-warn`,
      panneaux `.po-ok/.po-err/.po-muted`, légende carte `.cr-*` (tous définis) ;
      libellés FR cohérents entre boxes. RAS.

> **Tous les lots (0→5) sont terminés.** 5 boxes (Outils périmètre, Hydrologie,
> Bilan eau, Efficience, Diagnostic), 16 outils, gestionnaire de rendu unifié,
> couche masquée `bv_ouvrage_tete`. Reste à valider en **navigateur** (pas de
> runtime JS dans l'environnement de dev utilisé ici).

---

## 6. Fichiers touchés (synthèse)

| Fichier | Nature de l'intervention |
|---|---|
| [carte/layers.py](layers.py) | + couche(s) masquée(s) `bv_ouvrage_tete` |
| [carte/api_views.py](api_views.py) | filtrage `hidden` ; endpoints B1/B2/B3/C1/C3/D1… |
| [carte/urls.py](urls.py) | routes des nouveaux endpoints |
| `carte/static/carte/js/carte-rendu.js` | **nouveau** gestionnaire de rendu |
| `carte/static/carte/js/outils-*.js` | un fichier par box (ou extension) |
| [carte/static/carte/js/layout.js](static/carte/js/layout.js) | capture via `CarteRendu.getOverlay()` |
| `templates/carte/index.html` | items de box, sous-panneaux, fenêtres, CSS |
| `carte/OUTIL_*.md` | doc par outil |

Aucune migration (lecture seule + couche masquée pointant un modèle existant).

---

## 7. Points restants à valider

- **Q1 — Source réseau** de l'outil §3 : `carte.ReseauHydrographique` (Strahler)
  **ou** `ReseauOuvrageTete<Bassin>` (grid_code, Ziz/Moulouya peuplés) ?
- **Q2 — Sélection Hydrologie** : liste déroulante de BV (recommandé, couche
  masquée) **ou** sélection par clic sur les BV affichés par l'outil §3 ?
- **Q3 — Anti-désordre** : valider la règle « **un seul résultat actif** + slot
  contexte séparé » (vs autoriser plusieurs résultats nommés simultanés).
- **Q4 — Périmètre du premier jet** : exécuter **Lot 0 + Lot 1** d'abord
  (socle + Hydrologie, cœur de la demande), puis valider avant les lots 2–4 ?
- **Q5 — D1 efficience** : lire le dernier `Efficience` stocké, ou bouton
  « recalculer » (relance `calculer_efficience_complete`) ?

> Dès validation (au minimum Q1, Q2, Q4), je démarre par le **Lot 0** puis le
> **Lot 1**, en suivant strictement les 2 modules et le gestionnaire de rendu.
