# Plan d'insertion — Périmètres de Mibladen (Midelt)

> **Source** : `static/Perimetre Mibladen finale/diagnostic finalee.xlsx` (+ shapefiles `Perimetre Miblanden finale.shp`, `seguias Milbaden.shp`).
> **Cible** : app **`diagnostic`** (modèles `Perimetre`, `Seuil`/`EtatSeuil`, `MurProtection`/`EtatMurProtection`, `Seguias`/`TronconSeguia`/`EtatTronconSeguia`, `Assolement`, `TourEau`, `OrganisationAgriculteur`).
> **Contexte** : tous les périmètres sont en **commune de Mibladen**, **province de Midelt**, **coordination Midelt**. La commune `Mibladen` existe déjà dans `carte.Commune` (FK `Perimetre.commune` → `nom_fr='Mibladen'`).
> **Statut** : document de validation. Aucune écriture en base tant que ce plan n'est pas validé.

---

## 1. Volumétrie & PK attribuées

| Modèle | Nb d'enregistrements | Plage de PK proposée |
|---|---:|---|
| `Perimetre` | 13 | 1 → 13 |
| `Seuil` (+ `EtatSeuil`) | 13 | 1 → 13 |
| `MurProtection` (+ `EtatMurProtection`) | 1 | 1 |
| `Seguias` | 28 | 1 → 28 |
| `TronconSeguia` (+ `EtatTronconSeguia`) | 68 | 1 → 68 |
| `Assolement` | 53 | auto |
| `TourEau` | 37 | auto |
| `OrganisationAgriculteur` | 3 | auto |

Khettaras et Puits d'irrigation : **feuilles vides** (en-têtes seuls) → **rien à insérer**.

**Stratégie de PK** : `Perimetre`, `Seuil`, `MurProtection`, `Seguias` et `TronconSeguia` reçoivent un **PK entier explicite** (séquentiel) pour rendre les FK traçables dans ce plan. Les modèles `Etat*` sont en `OneToOneField(primary_key=True)` → **leur PK = celui de l'ouvrage parent** (`EtatSeuil.seuil_id = Seuil.pk`, etc.). Les tables enfants (`Assolement`, `TourEau`, `OrganisationAgriculteur`) gardent un PK **auto-incrément**.

> ⚠️ Le modèle `Perimetre` **n'a pas de champ `code`**. Le code métier de l'Excel (`MI.MIDE.MI005`…) ne peut donc pas être stocké tel quel : il sert uniquement de clé de correspondance ci-dessous. (À valider : faut-il l'ajouter dans `ksar_village` en suffixe ou créer un champ `code` ?)

### 1.1 Correspondance code métier → PK Périmètre

| PK | Code Excel | Ksar / village (`ksar_village`) | Nom usuel |
|---:|---|---|---|
| 1 | MI.MIDE.MI00 | Taghzout / Dmaya / Wllad Tayer | Taghzout / Dmaya / Wllad Tayer |
| 2 | MI.MIDE.MI001 | Dmaya | Dmaya |
| 3 | MI.MIDE.MI003 | Taghzout / Wlad Tayer | Taghzout / Wlad Tayer |
| 4 | MI.MIDE.MI004 | Wlad Tayer | Oum Terkat Wlad Tayer |
| 5 | MI.MIDE.MI005 | Ahouli | Ahouli |
| 6 | MI.MIDE.MI006 | Tadawt N'Ait Hourir | Tadawt N'Ait Hourir |
| 7 | MI.MIDE.MI009 | Takkat Ait Manssour | Ait Manssour |
| 8 | MI.MIDE.MI010 | Takkat | Takkat (Lfdil ben chrif) |
| 9 | MI.MIDE.MI011 | Ait Kaddour | Ait Ben Kaddour |
| 10 | MI.MIDE.MI012 | Takkat | Takkat (ighiz imnay) |
| 11 | MI.MIDE.MI013 | Takkat Ait Bouziane | Takkat Ait Bouziane |
| 12 | MI.MIDE.MI014 | Ait Moussa | Ait Moussa |
| 13 | MI.MIDE.MI015 | Sidi Said | Sidi Said |

---

## 2. Modèle `Perimetre` — mapping des champs

| Champ modèle | Colonne Excel (feuille `Perimetre`) | Transformation |
|---|---|---|
| `province` | Province | `"Midelt"` |
| `coordination` | Coordination | `"Midelt"` |
| `commune_territoriale` | Commune | `"Mibladen"` |
| `commune` (FK) | — | `carte.Commune(nom_fr='Mibladen')` (existant) |
| `ksar_village` | Ksar village | tel quel |
| `coordonnées X/Y` | X / Y | **Non stockées sur `Perimetre`** (pas de champ coord ; voir §9, géométrie via SHP) |
| `temperature_moyenne_annuelle` | Température moy. | vide → `null` |
| `precipitations_moyennes_annuelles` | Précipitations moy. | vide → `null` |
| `vent`, `humidite` | vent / Humidité | vide → `null` |
| `nombre_beneficiaires` | Nombre bénéficiaires | entier |
| `nombre_menages` | Nombre ménages | entier |
| `superficie_totale` | Superficie total | float |
| `superficie_agricole_utile` | Superficie agricole utile | float |
| `superficie_irriguee` | Superficie irriguée | float |
| `superficie_en_bour` | superficie en bour | float (0) |
| `type_de_sol` | Type de sol | `Argileux`→`argileux`, `Limon argileux`→`limoneux` *(à valider, voir §8)* |
| `niveau_de_fertilite` | Niveau de fertilité | `Bonne`→`bon` |
| `parcelles_moins_1ha` | < 1ha | **× 100** (fraction Excel → % ; convention app 0–100) |
| `parcelles_1_a_3ha` | Entre 1 a 3ha | **× 100** |
| `parcelles_plus_3ha` | > 3ha | **× 100** |
| `statut_juridique_melk` | Melk | **× 100** |
| `statut_juridique_collectif` | Collectif | **× 100** |
| `statut_juridique_location` | Location | **× 100** |
| `statut_juridique_guiche` | Guiche | **× 100** |
| `statut_juridique_habousse` | Habousse | **× 100** |
| `moyenne_bovins` | Moyenne bovins | float |
| `moyenne_ovins` | Moyenne ovins | float |
| `moyenne_caprins` | Moyenne caprins | float |
| `statut` | — | `'valide'` *(à confirmer — défaut DB `'brouillon'`)* |

---

## 3. Modèle `Seuil` (+ `EtatSeuil`) — 13 enregistrements

Un seuil par périmètre (feuille `Seuil`). `nom_du_seuil` est **unique** ✓ (13 noms distincts).

| PK Seuil | `perimetre_id` | `nom_du_seuil` | X (NM) | Y (NM) | Nature / Type |
|---:|---:|---|---|---|---|
| 1 | 5 | Sf Ahouli | 577310.995 | 248310.311 | Seuil de dérivation / En dur |
| 2 | 11 | Sf Ait Bouziane | 561522.219 | 236274.97 | Seuil de dérivation / En dur |
| 3 | 9 | Pl Ait Kaddour | 561658.263 | 237908.055 | Seuil de dérivation / En dur |
| 4 | 7 | Sf Ait Manssour | 561438.198 | 235058.666 | Seuil de dérivation / Fusible |
| 5 | 12 | Sd Ait Moussa | 561364.103 | 237047.381 | Seuil de dérivation / En dur |
| 6 | 6 | Sf Ait Ouhrir Akbab | 574827.418 | 252935.008 | Seuil de dérivation / En dur |
| 7 | 10 | Sf Ighiz Imnay | 561628.854 | 237333.607 | Seuil de dérivation / En dur |
| 8 | 8 | Sf Lfdil Ben Chrif | 561623.461 | 236732.546 | Seuil de dérivation / En dur |
| 9 | 2 | Pl Dmaya | 586935.242 | 249017.103 | Seuil de dérivation / Digue fusible |
| 10 | 1 | Laarja | 582581.36 | 249698.45 | Seuil de dérivation / En dur |
| 11 | 13 | Sf Sidi Said | 561304.969 | 240472.141 | Seuil de dérivation / En dur |
| 12 | 3 | S Taghzout | 582421.758 | 249880.618 | Seuil de dérivation / En dur |
| 13 | 4 | Sf Wlad Tayer | 582410.055 | 249894.249 | Digue de dérivation / Digue en dur |

**Mapping des champs** : `coordonnes_x/y` ← X/Y ; `nature_du_seuil`, `type_du_seuil`, `materiaux_de_construction` ← colonnes éponymes ; `debit_mobilise`←Débit ; `longueur`, `largeur_de_base`, `hauteur`, `largeur_tapis_amortissement` ← dimensions ; prises/dégrèvement droite-gauche ← blocs `L | l | Nbr Pertuis` ; `annee_derniere_rehabilitation` ← Année réhab ; texte d'origine `Etat de construction…` → champ legacy `etat_construction_fonctionnement`.

> ⚠️ **Champs requis sans valeur** : `debit_mobilise`, `longueur`, `largeur_de_base`, `hauteur`, `largeur_tapis_amortissement` sont `NOT NULL`. Pour les seuils détruits / sans mesures, on insère **`0`** par défaut (voir §8).

**`EtatSeuil`** (PK = PK Seuil) :
- `etat_construction_fonctionnement` (choix) ← texte « Mauvais / Moyen / Détruit… » mappé sur `ETAT_CONSTRUCTION_DIAG_CHOICES` (§8).
- `etat_materiel_hydromecanique` ← « Mauvais » → `mauvais`, vide → `''`.
- Les 10 notes 0–5 (`etat_structurel_digue`, `affouillement_aval`, `etat_vannes`, `infiltration_fuite`, `murs_guideaux`, `radier_aval`, `degradation_beton`, `limiteur_debit`, `envasement_retenue`, `dessableur`) ← colonnes notées de l'Excel, **transformées par inversion d'échelle + surcharges « détruit » (voir §8.5)**.

> ⚠️ **Correspondance des colonnes de notes à valider** (ordre Excel → champ) :
> `Etat structurel de la digue`→`etat_structurel_digue`, `Affouillement aval…`→`affouillement_aval`, `Etat et mobilité des vannes`→`etat_vannes`, `Infiltration/fuite`→`infiltration_fuite`, `Murs guideaux…`→`murs_guideaux`, `Radier aval…`→`radier_aval`, `Dégradation du béton`→`degradation_beton`, `Limiteur de débit…`→`limiteur_debit`, `Comblement de la retenue amont`→`envasement_retenue`, `Dessableur`→`dessableur`.

> 🔎 Les seuils préfixés `Pl …` (Pl Ait Kaddour, Pl Dmaya) sont dans la feuille **Seuil** → insérés comme `Seuil`. À confirmer s'il s'agit en réalité de **prises locales** (modèle `PriseLocale`).

---

## 4. Modèle `MurProtection` (+ `EtatMurProtection`) — 1 enregistrement

| Champ | Valeur |
|---|---|
| `pk` | 1 |
| `perimetre_id` | 4 (Oum Terkat Wlad Tayer) |
| `nom_mur_protection` | `M014-01` |
| `rive` | `droite` (Rive droite) |
| `position` | `amont` (Amont) |
| `nature_materiaux` | `Gabion` |
| `longueur` | 60 |
| `hauteur` | 1.2 |
| `epaisseur_superieure` | 0.6 |
| `epaisseur_inferieure` | 1 |
| `EtatMurProtection.etat_general` | `t_mauvais` (texte Excel = « Détruit », voir §8) |

> Le code ouvrage Excel `P014` / `M014-01` n'a pas de champ dédié → conservé dans `nom_mur_protection`.

---

## 5. Modèles `Seguias` / `TronconSeguia` / `EtatTronconSeguia`

L'Excel a **une ligne par tronçon**. On **regroupe par (périmètre, nom de séguia)** → 1 `Seguias` + N `TronconSeguia` + N `EtatTronconSeguia`.
**28 séguias distinctes**, **68 tronçons** au total.

`Seguias` : `nom_de_la_seguia` ← Nom seguias ; `type_deguia` ← Type (`Principale/Secondaire/Tertiaire` → `principale/secondaire/tertiaire`) ; `perimetre_id` ← périmètre.

`TronconSeguia` : `troncon`←Tronçon (TR1…) ; `longueur`←L(m) ; `largeur_meroire`←B(m) ; `hauteur`←H(m) ; `hauteur_eau`←Heau(m) ; `debit`←Débit(l/s) **converti en m³/s** (`/1000`) ; `fruit_de_berge`←Fruit de berge ; `epaisseur_parois`←Épaisseur parois ; `nature` (`Béton`→`beton`, `Béton armé`→`beton_arme`, `Terre`→`terre`, `Maçonnerie`→`autre`) ; `type_decoulement` (`À ciel ouvert`→`ciel_ouvert`, `Dalot`→`dalot`) ; `forme` non fournie → défaut `trapezoidale`.

`EtatTronconSeguia` : `etat_general` ← « État de construction… » mappé (§8.1) ; 7 notes 0–5 (`fissures_revetement`, `infiltration_fuite`, `obstructions_debris`, `erosion_berges`, `sedimentation_fond`, `ouvrages_regulation`, `spalling_beton`) ← colonnes éponymes, **transformées par inversion d'échelle (§8.5)**.

### 5.1 Liste des séguias (PK)

| PK | `perimetre_id` | Nom séguia | Type | Nb tronçons |
|---:|---:|---|---|---:|
| 1 | 5 | Saguia Ahouli | principale | 3 *(TR1–TR3)* |
| 2 | 5 | Saguia Mouzegar | secondaire | 1 |
| 3 | 5 | Saguia Boukhrib | secondaire | 1 |
| 4 | 5 | Saguia Iznagen | secondaire | 1 |
| 5 | 11 | Saguia Ait Bouziane | principale | 2 |
| 6 | 9 | Saguia Ait Ben Kaddour | principale | 3 |
| 7 | 7 | Saguia Ait Manssour | principale | 7 |
| 8 | 12 | Saguia Ait Moussa | principale | 2 |
| 9 | 6 | Saguia Ait Hourir | principale | 1 |
| 10 | 6 | Saguia Ait Hourir RD | secondaire | ⚠️ voir §7 |
| 11 | 6 | Saguia Ait Hourir RG | secondaire | ⚠️ voir §7 |
| 12 | 10 | Saguia Ait Bouziane | principale | 6 |
| 13 | 8 | Saguia Tamaourt | principale | 2 |
| 14 | 2 | Sagui Dmaya | principale | 3 |
| 15 | 1 | Saguia Laarja | principale | 11 |
| 16 | 13 | Saguia Sidi Said | principale | 1 |
| 17 | 3 | Saguia Charfa | principale | ⚠️ 4 (voir §7) |
| 18 | 3 | Saguia Hrara | secondaire | 2 |
| 19 | 3 | Saguia Laksar Lahmar | secondaire | 2 |
| 20 | 3 | Saguia Lmahfarri | secondaire | 1 |
| 21 | 4 | Saguia Oum Tektart | principale | 5 |
| 22 | 4 | Saguia Lwtaya | secondaire | 1 |
| 23 | 4 | Saguia Timounay | secondaire | 1 |
| 24 | 4 | Saguia Tania | secondaire | 2 |
| 25 | 4 | Saguia Lkaadi | secondaire | 2 |

> *(Numérotation 1→25 après consolidation des anomalies §7. Sans consolidation : 28 séguias.)*

> ✅ **Ahouli** : Saguia Ahouli possède bien **TR1 + TR2 + TR3** (la ligne TR1 / 447 m était la 1ʳᵉ ligne de données de la feuille). Point #7 résolu.
> ⚠️ **Débit `l/s` → `m³/s`** : `TronconSeguia.debit` est en m³/s. Les débits Excel (ex. 136 l/s) seront divisés par 1000 (→ 0.136). À valider.

---

## 6. Tables enfants du périmètre

### 6.1 `Assolement` (52 lignes)

`culture` ← Cultures (normalisées, §8.3) ; `pourcentage` ← Pourcentage cultures **× 100** (la convention de l'app est 0–100 : formulaire « Total … / 100 », bilan `pourcentage/100` — l'Excel donne des fractions 0–1) ; `rendement` ← Rendement ; `unite_rendement` (`kg/arbre`→`kg_arbre`, `q/ha` & `q`→`qx_ha`).

**`surface_ha` = `pourcentage` × `superficie_agricole_utile`** (du périmètre). La colonne « Surface » de l'Excel est exprimée en **« pied » (nombre d'arbres)** pour plusieurs périmètres et n'est donc pas une surface : c'est le **pourcentage qui fait foi**. La formule est cohérente avec les surfaces déjà en ha (ex. Ahouli Abricot `0.3 × 26 = 7.8 ha`, identique à l'Excel).

Exemples (Dmaya, SAU = 47 ha) : Pêche `0.25 × 47 = 11.75 ha` ; Abricot `11.75` ; Olive `11.75` ; Luzerne `0.13 × 47 = 6.11` ; Blé `5.64`.

> ℹ️ L'ancienne approche « pied ÷ densité de plantation » a été abandonnée : elle produisait des surfaces dépassant la SAU (Dmaya ≈ 163 ha vs 47 ha). `pourcentage × SAU` donne une surface réaliste et cohérente avec le périmètre.

### 6.2 `TourEau` (37 lignes)

`ayant_droit` ← Ayants droit eau ; `cycle_jours` ← Cycle tour eau (jours) ; `duree_heures` ← Durée tour eau (heures).

> ⚠️ La colonne « Cycle » contient parfois le **texte `Gravitaire`** au lieu d'un nombre (champ `cycle_jours` = `FloatField`). → ces lignes auront `cycle_jours = null` et l'information « Gravitaire » devra aller ailleurs (ex. à concaténer dans `ayant_droit`, ou champ note). À valider.
> Les lignes type « Tous Utilise Moteur Directement… » (sans valeurs) sont des **commentaires** : à insérer en `ayant_droit` (cycle/durée `null`) ou à ignorer. À valider.

### 6.3 `OrganisationAgriculteur` (3 lignes)

`nom` ← AUEA / Groupement traditionnel (noms en **arabe**, conservés tels quels en UTF-8).

| `perimetre_id` | `nom` |
|---:|---|
| 5 (Ahouli) | جمعية تمازيرت لمستخدمي الاغراض الزراعية |
| 5 (Ahouli) | جمعية تايمات للتنمية الاقتصادية و الاجتماعية |
| 4 (Oum Terkat Wlad Tayer) | جمعية الخوخة للتنمية والمبادرة |

> Vérification du formulaire `PerimetreForm` (diagnostic/forms.py) : les organisations sont saisies via le champ **`organisations_agriculteurs`** (textarea CSV de **noms** uniquement) → `OrganisationAgriculteur(perimetre, nom, ordre)`. Le modèle ET le formulaire ne gèrent donc **que `nom`**.
> Les colonnes Excel *Date de création, Dernier assemblé, Nb d'adhérents, Superficie, Mode d'irrigation, Classe de performance* **n'ont aucun champ cible**. **Décision (point #11) : importer le `nom` seulement** — ces 6 colonnes ne sont pas reprises et le modèle reste inchangé.

---

## 7. Anomalies de structure à arbitrer (séguias)

1. **Saguia Charfa éclatée** — l'Excel liste 4 noms `Saguia Charfa(tranch 1..4)`, chacun avec un seul tronçon `TR1..TR4`. → **Proposition : 1 seule séguia `Saguia Charfa` (principale) avec 4 tronçons TR1–TR4.** (Alternative : 4 séguias distinctes.)
2. **Saguia Ait Hourir RD / RG** (périmètre Tadawt N'Ait Hourir) — chacune apparaît **deux fois** : une ligne `Secondaire / TR1` **et** une ligne `Tertiaire / TR1`. Or `Seguias.type_deguia` est unique par séguia et `(seguia, troncon)` doit être unique. **Conflit.** → **Proposition : séparer en deux séguias par rive** : `…RD (secondaire)` + `…RD tertiaire (tertiaire)` (idem RG), ou renommer le tronçon tertiaire en `TR2`. À trancher.

---

## 8. Règles de transformation transverses

### 8.1 État « Détruit » → échelle de diagnostic
`ETAT_CONSTRUCTION_DIAG_CHOICES` n'a pas de niveau « Détruit ». Mapping retenu :

| Texte Excel | `etat_general` |
|---|---|
| Détruit / Détruit complètement / Détruit par la crue / Mauvais à détruit | `t_mauvais` |
| Mauvais | `mauvais` |
| Moyen à mauvais | `moyen_mauvais` |
| Moyen | `moyen` |
| Moyen à bon | `moyen_bon` |
| Bon | `bon` |

Le texte d'origine est conservé dans le champ **legacy** `etat_construction_fonctionnement` / `etat_construction`. Le traitement des **notes 0–5** des ouvrages détruits est décrit en **§8.5** (et non « tout à 0 »).

### 8.2 Valeurs numériques manquantes
Champs `NOT NULL` sans valeur Excel (dimensions de seuils détruits, etc.) → **`0`**. Champs `null=True` vides → `null`.

### 8.3 Cultures — normalisation vers `CULTURES_TAFILALET`

| Excel | Référentiel |
|---|---|
| Pêche | `Peche` |
| Olivier | `Olive` |
| Blé dur | `Blé` |
| Abricot, Luzerne | inchangé |
| **Maïs** | **`Mais` — à AJOUTER au référentiel** |

> ⚠️ **Changement de code requis** : ajouter `("Mais", "Maïs")` à la constante `CULTURES_TAFILALET` dans [diagnostic/models.py](../../diagnostic/models.py) **puis générer une migration** (`makemigrations diagnostic`). Réutilisé automatiquement par `Besions_Ressources.Kc_Kr_culture`.

### 8.4 Coordonnées
X/Y de l'Excel sont en **Nord Maroc (EPSG:26191)** → stockées dans `coordonnes_x/y` (seuils). Géométrie WKT en SRID 4326 non générée dans ce lot (import ultérieur via les vues SHP).

> ⚠️ **Coordonnées malformées MI011** (périmètre Ait Ben Kaddour) : Excel `X=561674604`, `Y=237940594` (séparateur décimal absent). → correction proposée **`561674.604` / `237940.594`** (cohérent avec le seuil Pl Ait Kaddour à 561658 / 237908). À valider.

### 8.5 Notes 0–5 du diagnostic — inversion d'échelle + surcharges « détruit »

**S'applique à `EtatSeuil` (10 notes) ET `EtatTronconSeguia` (7 notes).**

L'échelle des notes de l'Excel est **inversée** par rapport aux modèles :
- **Excel** : `5` = meilleur état / `1` = très mauvais / `0` = élément absent ou non évalué.
  *(Vérifié : une séguia notée « Bon » porte 5/4/4… ; un ouvrage « Détruit » porte 0/0/0.)*
- **Modèle** (`NOTE_CHOICES` / `NOTE_SEGUIA_CHOICES`) : `0` = aucun désordre / état normal … `5` = critique.

**Règle 1 — inversion (base, toutes les notes)** :
```
note_modèle = 0            si note_Excel == 0      (absence / non évalué → 0 = aucun désordre)
note_modèle = 5 - note_Excel   sinon
```
Ex. Excel 5 → 0, 4 → 1, 3 → 2, 2 → 3, 1 → 4.

**Règle 2 — « Détruit complètement »** (texte `etat_general` contient *« détruit complètement »*, ex. *« Détruit complètement par la crue »*) :
→ **toutes les notes de l'ouvrage = 5** (critique). Surcharge la règle 1.

**Règle 3 — « Détruit par la crue »** (texte contient *« détruit »* + *« crue »*, **sans** *« complètement »*, ex. MI015 *« Détruit par la crue »*) :
→ **`etat_structurel_digue` = 5, `degradation_beton` = 5, `infiltration_fuite` = 5** ; les autres notes suivent la règle 1.

**Ordre d'application** : Règle 1 (base) → puis Règle 2 **ou** Règle 3 selon le texte (Règle 2 prioritaire si « complètement » présent).

| Texte `etat_general` (Excel) | Notes appliquées |
|---|---|
| Détruit complètement / Détruit complètement par la crue | Règle 2 → **toutes = 5** |
| Détruit par la crue | Règle 3 → **digue, béton, infiltration = 5** ; reste = Règle 1 |
| Tous les autres (Mauvais, Moyen, Bon, Mauvais à détruit, vide…) | Règle 1 seule |

> ⚠️ **Mur de protection** (M014-01, texte = *« Détruit »* seul) : l'Excel ne fournit pas de notes chiffrées et le texte n'est ni « complètement » ni « par crue ». **Proposition : appliquer l'esprit de la règle 2** → `fissures_revetement = degradation_beton = risque_contournement = 5`. À confirmer (point #15).
> 🔎 Les colonnes de l'Excel concernées sont **déjà 0–5**, donc seule la transformation ci-dessus s'applique (pas de re-notation manuelle).

---

## 9. Géométrie (intégrée à l'import)
Les géométries sont importées par la même commande `import_mibladen`, **reprojetées de Nord Maroc (EPSG:26191) vers WGS84 (4326)** et aplaties en 2D (`WKBWriter(outdim=2)`).

- **`Seuil.geometrie`** (Point) ← coordonnées X/Y de l'Excel, converties 26191→4326. **13/13** (ex. Sf Ahouli → lon −4.572 / lat 32.828). Aucune dépendance au shapefile.
- **`Perimetre.geometrie`** (Polygon) ← `Perimetre Miblanden finale.shp` (12 features), jointure sur `nom_de_per`. **12/13** — seul **MI00 « Taghzout / Dmaya / Wllad Tayer »** est absent du shapefile.
- **`TronconSeguia.geometrie`** (LineString) ← `seguias Milbaden.shp` (58 lignes), jointure best-effort par (périmètre + nom canonique de séguia + ordre). **57/68**. ⚠️ Les attributs joints du shapefile (Nom_seguia, Tronçon, dimensions, notes) sont **corrompus** par une jointure spatiale ratée → seules la **géométrie** + `Nom_ségui` + `Code` + `Numéro` sont utilisées. Les **11 tronçons sans géométrie** appartiennent tous à **Saguia Laarja (MI00)**, périmètre également absent du shapefile.

> Bilan : la seule lacune géométrique est le périmètre **MI00**, manquant dans les deux shapefiles (polygone + lignes). À fournir séparément si nécessaire.

> 🐞 **Correctif affichage carte** : le contour des périmètres apparaissait « simplifié » dans le module Carte alors que la donnée est fidèle (3499 pts conservés du shapefile à l'API). Cause = simplification Douglas-Peucker par défaut des sources GeoJSON de **MapLibre** (`tolerance: 0.375`). Corrigé en ajoutant `tolerance: 0` aux sources dans [carte/static/carte/js/layers.js](../../../carte/static/carte/js/layers.js) et [carte/static/carte/js/drilldown.js](../../../carte/static/carte/js/drilldown.js). (Recharger la page avec vidage du cache JS.)

---

## 10. Ordre d'insertion (intégrité FK)
1. `carte.Commune('Mibladen')` — **pré-requis existant** (vérifier l'orthographe exacte en base).
2. Référentiel : **ajout `Mais`** + migration (§8.3).
3. `Perimetre` (PK 1→13).
4. `Seuil` (PK 1→13) → `EtatSeuil`.
5. `MurProtection` (PK 1) → `EtatMurProtection`.
6. `Seguias` (PK 1→25/28) → `TronconSeguia` (PK 1→68) → `EtatTronconSeguia`.
7. `Assolement`, `TourEau`, `OrganisationAgriculteur`.

---

## 11. Récapitulatif des points à valider

| # | Point | Proposition par défaut |
|---:|---|---|
| 1 | Stockage du code métier `MI.MIDE.*` (pas de champ) | Référence seule, non stocké |
| 2 | `statut` des enregistrements | `valide` |
| 3 | Seuils `Pl …` = Seuil ou PriseLocale ? |Seuils|
| 4 | Correspondance exacte des 10 colonnes de notes du seuil | cf. §3 |
| 5 | Saguia Charfa : 1 séguia / 4 tronçons | 1 séguia + TR1–TR4 |
| 6 | Saguia Ait Hourir RD/RG (conflit Sec./Tert.) | dédoubler par rive |
| 7 | Ahouli : tronçon TR1 | ✅ Résolu — TR1 présent (1ʳᵉ ligne) : insérer TR1+TR2+TR3 |
| 8 | Débit séguia `l/s` → `m³/s` (÷1000) | oui |
| 9 | `surface_ha` de l'assolement | ✅ Corrigé — `surface_ha = pourcentage × superficie_agricole_utile` (la colonne « Surface » en pied n'est pas une surface ; cohérent avec les ha fournis) |
| 10 | `TourEau` : valeur « Gravitaire » et lignes-commentaires | cycle `null`, texte dans `ayant_droit` |
| 11 | Colonnes `OrganisationAgriculteur` (date création, dernier assemblé, nb adhérents, superficie, mode irrigation, classe perf.) | ✅ Tranché — **importer le `nom` seulement**. Les 6 colonnes ne sont pas reprises (pas de champ cible ; modèle inchangé). |
| 12 | Coord. MI011 malformées | 561674.604 / 237940.594 |
| 13 | `type_de_sol` « Limon argileux » → `limoneux` | oui |
| 14 | **Notes 0–5 (seuils & tronçons)** : inversion d'échelle + surcharges « détruit » | ✅ Règle 1 `5−valeur` (0→0) ; Règle 2 détruit complètement → tout=5 ; Règle 3 détruit par crue → digue+béton+infiltration=5 (§8.5) |
| 15 | Mur « Détruit » (sans notes chiffrées) | 3 notes = 5 (esprit règle 2) — appliqué |
| 16 | **Géométries (shp)** | ✅ Importées : Seuil 13/13 (coords 26191→4326), Périmètre 12/13, Tronçon 57/68. Lacune = MI00, absent des deux shapefiles |
| 17 | **Pourcentages en % (0–100)** | ✅ Corrigé — `pourcentage` (assolement), `parcelles_*`, `statut_juridique_*` stockés ×100 (l'Excel donne des fractions 0–1, mais formulaire/bilan attendent 0–100 → « Total … / 100 » désormais correct). `surface_ha` inchangé. NB : Ahouli somme à 90 % côté source (assolement incomplet dans l'Excel), pas un bug |
