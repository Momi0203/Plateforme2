# Proposition — Boxes & Outils du panneau « Outils » de la Carte

> **Statut : à valider avant exécution.**
> Ce document propose de nouvelles **boxes** (groupes accordéon) et **outils**
> pour le panneau droit **Outils** de la carte (`/carte/`), en réutilisant les
> fonctions de calcul des **4 apps** (`diagnostic`, `analyse_hydrologique`,
> `Besions_Ressources`, `efficiences`).
>
> Règles imposées :
> 1. **Importer les fonctions** des 4 apps (ne pas réimplémenter la logique).
> 2. **Reprendre les 2 outils existants comme modules** (mode de sélection,
>    forme du sous-panneau, modes de présentation du résultat).
> 3. Outils **simples** (au plus « peu complexes ») — le détail fin reste du
>    ressort des 4 apps.
> 4. **Aucun lien de navigation** vers les 4 apps : les outils lisent les données
>    et calculent **dans la carte**.

---

## 1. Les 2 modules réutilisables (extraits des outils existants)

Les deux outils déjà livrés définissent **deux patrons** que tous les nouveaux
outils reprennent tels quels.

### Module A — « Rendu thématique sur carte » (patron : outil **Besoin**)

- **Sélection** : `window.selection_par_couche.<couche>` (clic / rectangle /
  requête) ; si vide → **toute la couche**.
- **Sous-panneau** (style `po-panel-*`) : compteur de sélection (lecture seule),
  liste **Année** (optionnelle), liste **Mode de présentation**, bouton
  **Exécuter**, bouton **Effacer**, zone **Résultat / Légende**.
- **Modes de présentation** : `point_valeur` (cercle classé quantiles),
  `cercle_prop` (cercle proportionnel √), `camembert` (3 années), `barres`
  (3 années), `choroplethe` (aplat sur le polygone/la ligne).
- **Rendu** : `maplibregl.Marker` (DOM/SVG, toujours au-dessus du canvas) +
  recoloration WebGL ; légende contextuelle ; `window.get<Outil>Overlay()` pour
  la capture **Layout/PDF** ; bouton **Effacer**.
- **API** : `GET …` → **FeatureCollection** de Points (`point_on_surface`,
  EPSG:4326) + propriétés (valeur(s)).
- Réf. : [OUTIL_BESOIN.md](OUTIL_BESOIN.md).

### Module B — « Fenêtre flottante déplaçable » (patron : outil **Comparaison besoin**)

- **Sélection** : identique au Module A.
- **Sous-panneau** : compteur, liste **Année** (optionnelle), éventuel
  avertissement de plafond, bouton **Générer le graphique**.
- **Résultat** : fenêtre flottante `#cb-window` (ou clone) **déplaçable**
  (drag sur l'en-tête) et **redimensionnable**, contenant un **graphe Chart.js**
  (+ table facultative) ; fermeture par la croix. **Plafond** (ex. 25 entités).
- **API** : `GET …` → **JSON** `{ count, total, tronque, items: [...] }`.
- Réf. : [OUTIL_COMPARAISON_BESOIN.md](OUTIL_COMPARAISON_BESOIN.md).

> **Convention de données** : pour rester simples, les outils **lisent en
> priorité les résultats déjà calculés et stockés** par les apps
> (`ResultatAnalyseHydrologique`, `BilanBesoinRessources`, `Efficience`,
> champs `volume_*`, `efficience_calculee`…). Ils ne lancent un **calcul à la
> volée** que pour des fonctions **légères et sans paramètres lourds** (Tc, ET0,
> efficience par cascade). Les analyses paramétrées complètes restent dans les apps.

---

## 2. Ce qui existe déjà (à NE PAS redoubler)

| Existant | Type | Source |
|---|---|---|
| **Besoin** (volume `volume_annee_*`) | Module A | `perimetres_besoin_points` |
| **Comparaison besoin** (besoin/excédent/déficit) | Module B | `perimetres_comparaison_besoin` |
| **Indice de priorité** (scoring `Etat*`, 0–100 %) | Module A | `indice_priorite` |
| **Scoring** (Jenks / quantile pondéré) | calcul | `outil_scoring` |
| **Efficience tronçon** (calcul + persistance) | calcul | `outil_efficience` |
| **Manning** (capacité tronçon) | calcul | `outil_manning` |
| **Buffer / Intersection** | géo | `outil_buffer`, `outil_intersection` |
| **Apport crue par ouvrage** (seuil/prise/barrage → BV) | data | `*_bv_apport` |
| **Rendement / Tours d'eau / Volume bilan** (périmètre) | data | `perimetre_*` |

Les propositions ci-dessous **réutilisent** ces endpoints quand c'est pertinent
(repérés « ♻ réutilise »).

---

## 3. Logique des 4 apps — fonctions importables

### `diagnostic` (pas de `calculs.py` → app **data-centric**)
- Entité pivot **`Perimetre`** + 7 ouvrages + modèles **`Etat<X>`** (notes 0–5
  `NOTE_CHOICES`, `etat_general` `ETAT_CONSTRUCTION_DIAG_CHOICES`).
- `Assolement` (culture, `surface_ha`, `rendement`, `pourcentage`).
- Débits/dimensions par ouvrage (`debit_mobilise`, `debit_derive`, `debit`…).
- Logique de notation déjà exposée par `indice_priorite` / `outil_scoring`.

### `analyse_hydrologique.calculs`
- `run_analyse`, `recalculer_depuis_tc/_q` (analyse paramétrée — **lourde**).
- `calculer_apports_crue_sans_prelevement(station_hydro, tc_h)` → 12 mois × 3 années.
- `bv_to_hydro` + `calculer_tc_bv` (via `hydrologie_bv`) → Tc par formule.
- Constantes `FORMULES_TC/Q_DISPONIBLES`, `PERIODES = [10,20,50,100]`.
- Modèle **`ResultatAnalyseHydrologique`** (`qcrue_t10..t100`,
  `temps_concentration`, `details_calcul`).

### `Besions_Ressources.calculs`
- `calculer_eto(temperatures, taux_insolation, latitude)` + `taux_insolation_par_latitude`.
- `pluie_efficace`, `calculer_besoins_culture`, `bilan_global`, `calculer_apports_bilan`.
- Modèle **`BilanBesoinRessources`** (`resultats_bilan_normale/humide/seche`,
  `resultats_eto/cultures/crue`), `StationClimatique`, `Kc_Kr_culture`.

### `efficiences.services`
- `calculer_efficience_complete(perimetre, type, id)` (orchestrateur : cascade
  tronçon → P/S/T → globale, **persiste** un `Efficience`).
- `calculer_efficience_troncon(troncon, …)` (Pi/Pv, débit amont→aval).
- Modèle **`Efficience`** (`efficience_globale`, `efficience_principale/secondaire/tertiaire`).

---

## 4. Propositions de boxes & outils

### 🅐 Box « Diagnostic ouvrages » — app `diagnostic`

| # | Outil | Module | Sélection | Entrées | Sortie | Données | Endpoint proposé | Cplx |
|---|---|---|---|---|---|---|---|---|
| A1 | **Assolement du périmètre** | B | 1 périmètre | — | Camembert des surfaces par culture + rendement pondéré + culture dominante | Lecture `Assolement` ♻ `perimetre_rendement` | (réutilise l'existant) | ⭐ |
| A2 | **Comparaison d'état des ouvrages** | B | ouvrages d'1 couche (≤25) | couche | Barres empilées : nb d'ouvrages par classe d'état (`etat_general`) | Lecture `Etat<X>` | `GET api/ouvrages/etat-comparaison/?couche=&pks=` | ⭐⭐ |
| A3 | **Débit mobilisé des ouvrages** | A | 1 couche d'ouvrages | mode (cercle_prop / point_valeur) | Cercles ∝ débit (`debit_mobilise`/`debit_derive`/`debit`) | Lecture champ débit | `GET api/ouvrages/debit-points/?couche=&pks=` | ⭐ |

*Note : la coloration par `etat_general` pur est déjà faisable via la Symbologie
et l'Indice de priorité — d'où le choix de la **comparaison agrégée** (A2),
à valeur ajoutée, plutôt qu'une énième coloration d'état.*

### 🅑 Box « Hydrologie / Crues » — app `analyse_hydrologique`

| # | Outil | Module | Sélection | Entrées | Sortie | Données | Endpoint proposé | Cplx |
|---|---|---|---|---|---|---|---|---|
| B1 | **Débits de crue (T)** | B | 1 bassin versant | — | Barres Q10/Q20/Q50/Q100 (dernière analyse) | Lecture `ResultatAnalyseHydrologique.qcrue_t*` | `GET api/bv/<pk>/crue-periodes/` | ⭐ |
| B2 | **Temps de concentration** | B | 1 bassin versant | — | Barres Tc par formule + moyenne | **Calcul** `calculer_tc_bv` (import) | `GET api/bv/<pk>/tc/` | ⭐⭐ |
| B3 | **Apports de crue mensuels** | B | 1 station hydrométrique | — | 12 mois Sep→Aoû × 3 années (volumes) | **Calcul** `calculer_apports_crue_sans_prelevement` (import) ; Tc du BV lié | `GET api/station-hydro/<pk>/apports-crue/` | ⭐⭐ |
| B4 | **Crue de projet (carte)** | A | bassins versants | mode + période T | Cercles/aplat ∝ Q(T) par BV | Lecture analyses stockées | `GET api/bv/crue-points/?t=100&pks=` | ⭐⭐ |

### 🅒 Box « Bilan eau » — app `Besions_Ressources`

| # | Outil | Module | Sélection | Entrées | Sortie | Données | Endpoint proposé | Cplx |
|---|---|---|---|---|---|---|---|---|
| C1 | **Bilan mensuel besoins/ressources** | B | 1 périmètre | année (normale/humide/sèche) | Graphe 12 mois : besoins vs ressources + déficit/excédent | Lecture `BilanBesoinRessources.resultats_bilan_<annee>` | `GET api/perimetre/<pk>/bilan-mensuel/?annee=` | ⭐ |
| C2 | **Taux de couverture des besoins** | A | périmètres | mode (choroplèthe/points) | % couverture = ressources/besoins par périmètre | Lecture totaux du dernier bilan | `GET api/perimetres/couverture/?pks=` | ⭐⭐ |
| C3 | **ET0 climatique** | B | 1 station climatique | — | Courbe ET0 mensuelle (12 mois) | **Calcul** `calculer_eto` + `taux_insolation_par_latitude` (import) | `GET api/station-clim/<pk>/eto/` | ⭐ |

### 🅓 Box « Efficience réseau » — app `efficiences`

| # | Outil | Module | Sélection | Entrées | Sortie | Données | Endpoint proposé | Cplx |
|---|---|---|---|---|---|---|---|---|
| D1 | **Efficience d'un ouvrage de tête** | B | 1 ouvrage de tête (seuil/prise/khettara/forage/barrage) | — | Barres cascade P / S / T + jauge globale | Lecture dernier `Efficience` (option : recalcul `calculer_efficience_complete`) | `GET api/ouvrage-tete/<type>/<pk>/efficience/` | ⭐⭐ |
| D2 | **Profil de pertes d'une séguia** | B | tronçons d'1 séguia | — | Profil débit amont→aval + Pi/Pv par tronçon | **Calcul** `calculer_efficience_troncon` ♻ `outil_efficience` | (réutilise + présentation profil) | ⭐⭐ |
| D3 | **Rendement des tronçons (carte)** | A | tronçons de séguias | mode choroplèthe (lignes) | Lignes colorées par `efficience_calculee` (quantiles) | Lecture champ persistant | `GET api/troncons/rendement-points/?pks=` | ⭐ |

---

## 5. Récapitulatif

- **4 boxes** (une par app) + la box existante **« Outils périmètre »**
  (Besoin, Comparaison besoin).
- **13 outils** proposés : **5** en Module A (carte), **8** en Module B (fenêtre).
- **Fonctions importées** : `diagnostic` (modèles + scoring existant),
  `analyse_hydrologique.calculs` (Tc, apports crue), `Besions_Ressources.calculs`
  (ET0, bilans), `efficiences.services` (cascade, tronçon).
- **Réutilisation** : A1 ♻ `perimetre_rendement`, D2 ♻ `outil_efficience` ; les
  outils « carte » clonent la mécanique de **Besoin**, les outils « fenêtre »
  celle de **Comparaison besoin**.
- **Aucun lien** vers les pages des 4 apps.

---

## 6. Points à valider (avant exécution)

1. **Périmètre de livraison** : tout (13 outils) ou un sous-ensemble prioritaire ?
   *(Recommandation : commencer par C1, B1, D1, A1 — fort impact, faible
   complexité, lecture de données déjà calculées.)*
2. **Lecture vs recalcul** : confirmer le principe « lire le dernier résultat
   stocké » (B1, B4, C1, C2, D1) plutôt que relancer les analyses paramétrées.
3. **Comportement si aucune donnée** : un ouvrage/périmètre **sans analyse ni
   bilan** doit-il être ignoré (silencieux) ou signalé dans la légende/fenêtre ?
4. **Plafond Module B** : garder **25** entités (comme Comparaison besoin) ?
5. **Découpage des boxes** : 4 boxes distinctes (1/app) **ou** regrouper sous 2
   boxes « Analyse hydraulique » et « Diagnostic & bilan » ?
6. **Noms définitifs** des boxes/outils (libellés français ci-dessus à confirmer).

> Après validation de ces points, j'implémente outil par outil en suivant
> exactement les 2 modules (sélection, sous-panneau, endpoint, rendu) + une
> doc `OUTIL_<NOM>.md` par outil, comme pour Besoin / Comparaison besoin.
