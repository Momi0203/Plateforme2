---
section: "05"
titre: "Panneau droit — Outils génériques et boîtes métier"
version: "2.0"
date: "2026-06-04"
tags: [outils, analyse, scoring, efficience, Manning, Répéter]
---

# §5.3 — Panneau droit

Panneau vertical escamotable (280 px). Barre de recherche en haut, onglets Favoris / Récents, boîtes à outils.

---

## 5.3.1 Outils génériques (SIG transversaux)

| Boîte | Outils |
|---|---|
| **Analyse** | Tampon (Buffer), Intersection, Union, Découpage (Clip), Proximité Near, Sélection par localisation |
| **Gestion des données** | Fusion (Merge), Dissolution (Dissolve), Jointure spatiale, Calculer un champ, Sélection par attribut |
| **Conversion** | Export GeoJSON, Export Shapefile (ZIP), Export CSV attributaire |
| **Statistiques spatiales** | Résumé par zone, Fréquences par catégorie, Densité de points par polygone, Heatmap |

---

## 5.3.2 Boîtes à outils métier

> **Outil Répéter** : présent dans toutes les boîtes sauf Périmètre.
> Applique l'analyse courante à toutes les entités sélectionnées en batch.
> Barre de progression + log par entité. Export tableau comparatif.

---

### Box Périmètre

#### Outil 1 — Classification déficitaire / excédentaire

Classe les périmètres selon leur bilan en eau.

```
Inputs :
  - Couche : perimetres (sélection ou tous)
  - Type d'année : normale | humide | sèche
  - Mois de référence : Sep … Août (1-12)

Source Django :
  BilanBesoinRessources.resultats_bilan_normale  (JSON)
  BilanBesoinRessources.resultats_bilan_humide   (JSON)
  BilanBesoinRessources.resultats_bilan_seche    (JSON)

Output : couche colorée vert (excédent) / rouge (déficit)
```

#### Outil 2 — Classification par culture ou surface

```
Inputs :
  - Couche : perimetres
  - Critère : culture dominante | superficie_irriguee

Source Django :
  Assolement.culture, Assolement.pourcentage → culture avec max(pourcentage)
  Perimetre.superficie_irriguee

Output : carte choroplèthe + légende dynamique
```

#### Outil 3 — Indice de priorisation (Score périmètre)

```
PRINCIPE :
  Score = Σ(coefficient_i × valeur_normalisée_i)

Critères disponibles (l'utilisateur fixe le coefficient 0-5 pour chacun) :
  - superficie_irriguee          (Perimetre)
  - nombre_beneficiaires         (Perimetre)
  - superficie_en_bour           (Perimetre)
  - taux_ouvrages_degrades       (% ouvrages avec etat_general ≤ 'moyen_mauvais')
  - volume_deficitaire_moyen     (BilanBesoinRessources)

Paramètres :
  - N classes : 3, 4 ou 5
  - Méthode : Jenks | Quantile

Output : carte choroplèthe + tableau des scores + export Excel
Action : bouton "Exécuter"
```

---

### Box Seuil

#### Outil 1 — Score ouvrage / Indice de priorité

```
Critères (EtatSeuil — notes 0-5, coefficient fixé par l'utilisateur) :
  etat_structurel_digue, affouillement_aval, envasement_retenue,
  murs_guideaux, radier_aval, etat_vannes, dessableur,
  degradation_beton, infiltration_fuite, limiteur_debit

Score = Σ(coefficient_i × note_i) / Σ(coefficients × 5) × 100

Output : couche colorée par score + tableau
Action : bouton "Recherche" ou "Exécuter"
```

#### Outil 2 — Répéter
Applique le score à tous les seuils sélectionnés en batch.

#### Outil 3 — Statistiques débit
Histogramme `Seuil.debit_mobilise` (l/s) + min/max/moy/médiane.

#### Outil 4 — Carte efficience réseau
Choroplèthe `Seuil.efficience_reseaux` (0–1). Rampe rouge→vert.

---

### Box Séguia / Tronçon

#### Outil 1 — Efficience des tronçons (PI + PV)

```
Déclenche le recalcul d'efficience pour les tronçons sélectionnés.
Appelle les fonctions existantes dans la plateforme.

Formules :
  PI = Perte Infiltration (m³/s) = f(nature, longueur, dimensions)
  PV = Perte Évaporation (m³/s) = f(surface_mouillée, ET0)
  Efficience (%) = (Q_entrée − PI − PV) / Q_entrée × 100

Paramètre supplémentaire :
  ET0 (mm/jour) → lue depuis Perimetre.et0_mm_jour

Résultats écrits dans :
  TronconSeguia.efficience_calculee
  TronconSeguia.perte_infiltration_m3s
  TronconSeguia.perte_vaporisation_m3s
  TronconSeguia.date_dernier_calcul

Action : bouton "Calculer"
```

#### Outil 2 — Débit Manning du tronçon

```
Formule Manning-Strickler :
  Q = (1/n) × A × R^(2/3) × S^(1/2)

Paramètres lus depuis TronconSeguia :
  forme, longueur, largeur_meroire, hauteur_eau,
  fruit_de_berge, epaisseur_parois, diametre

Paramètre utilisateur :
  n (Manning) : saisi ou valeur par défaut selon nature :
    béton : 0.013, béton armé : 0.014, terre : 0.025

Output : Q calculé affiché dans panel + colonne dans le tableau
Action : bouton "Calculer"
```

#### Outil 3 — Score ouvrage / Indice de priorité

```
Critères (EtatTronconSeguia — notes 0-5) :
  fissures_revetement, infiltration_fuite, obstructions_debris,
  erosion_berges, sedimentation_fond, ouvrages_regulation, spalling_beton

Même formule que Box Seuil.
```

#### Outil 4 — Répéter
Batch efficience + Manning + score sur tous les tronçons sélectionnés.

---

### Box Prise Locale

#### Outil 1 — Score ouvrage

```
Critères (EtatPriseLocale — notes 0-5) :
  envasement_sedimentation_entree, degradation_revetement,
  accumulation_debris_vegetation, etat_dispositifs_regulation,
  protection_crues_debordements
```

#### Outil 2 — Répéter

#### Outil 3 — Débit dérivé vs besoin
Compare `PriseLocale.debit_derive` avec besoin périmètre associé (BilanBesoinRessources).

---

### Box Barrage Collinaire

#### Outil 1 — Score ouvrage

```
Critères (EtatBarrageRetenue — notes 0-5) :
  affouillement_pied_digue_aval, taux_envasement_retenue,
  regulation_debits_aval, fonctionnement_ouvrages_prise_eau
```

#### Outil 2 — Répéter

#### Outil 3 — Bilan volume apports vs besoins
Compare `BilanOuvrageAssocie.apports_mensuels_*` avec besoins mensuels.
Graphique barres empilées 12 mois Sep→Août pour 3 types d'années.

---

### Box Puits / Forage

#### Outil 1 — Score ouvrage

```
Critères (EtatForagePuits — notes 0-5) :
  qualite_physico_chimique_eau, degradation_structurelle_forage,
  colmatage_forage, etat_equipements
```

#### Outil 2 — Répéter

#### Outil 3 — Comparaison par source d'énergie
Camembert `ForagePuits.source_energie_pompage` (réseau/solaire/diesel/hybride).

---

### Box Khettarat

#### Outil 1 — Score ouvrage

```
Critères (EtatKhettara — notes 0-5) :
  envasement_ensablement_fond, degradation_beton,
  accessibilite_entretien, stabilite_galerie_principale
```

#### Outil 2 — Répéter

#### Outil 3 — Carte débit vs longueur
Scatter `Khettara.debit` vs `Khettara.longueur` + cercles proportionnels au débit.

---

## 5.3.3 Exigences transversales sur tous les outils

| ID | Exigence | Priorité |
|---|---|---|
| OUT-01 | Formulaire modal avec description + aide contextuelle par champ | MUST |
| OUT-02 | Barre de progression pendant exécution | SHOULD |
| OUT-03 | Log d'exécution consultable (messages, durée, erreurs) | SHOULD |
| OUT-04 | Résultat = nouvelle couche ajoutée au gestionnaire (nom modifiable) | MUST |
| OUT-05 | Historique 5 derniers outils avec paramètres mémorisés | SHOULD |
| OUT-06 | Système de favoris (épingler outil) | SHOULD |
| OUT-07 | Barre de recherche en temps réel sur nom des outils | MUST |

## 5.3.4 Calculatrice de champ

| ID | Exigence | Priorité |
|---|---|---|
| CF-01 | Éditeur multi-lignes avec coloration syntaxique | SHOULD |
| CF-02 | Fonctions : arithmétiques, texte, date, géométriques (ST_Length, ST_Area) | SHOULD |
| CF-03 | Aperçu valeur calculée sur 5 entités avant application | SHOULD |
| CF-04 | Résultat = champ calculé non persistant par défaut (éditeur peut persister) | SHOULD |
