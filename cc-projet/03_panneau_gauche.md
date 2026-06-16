---
section: "03"
titre: "Panneau gauche — Contrôle de visualisation"
version: "2.0"
date: "2026-06-04"
tags: [UI, couches, sélection, requête, symbologie, drill-down]
---

# §5.1 — Panneau gauche

Panneau vertical escamotable, largeur par défaut 280 px. Six onglets.

---

## 5.1.1 Onglet Couches

| ID | Exigence | Priorité |
|---|---|---|
| PG-01 | Arborescence hiérarchique par groupes : Administratif / Hydrologie / Diagnostic | MUST |
| PG-02 | Case à cocher par couche pour basculer la visibilité | MUST |
| PG-03 | Glisser-déposer pour réordonner les couches | SHOULD |
| PG-04 | Icône du type géométrique (point / ligne / polygone) à gauche du nom | MUST |
| PG-05 | Badge rouge si erreur de chargement de la couche | SHOULD |
| PG-06 | Menu contextuel clic droit : Zoomer vers, Voir tableau, Ouvrir symbologie | MUST |
| PG-07 | Tooltip : nombre d'entités chargées par couche | COULD |

---

## 5.1.2 Onglet Sélection

| ID | Exigence | Priorité |
|---|---|---|
| SEL-01 | Sélection rectangulaire (drag) | MUST |
| SEL-02 | Sélection circulaire (centre + rayon) | SHOULD |
| SEL-03 | Sélection polygonale libre (clic point par point) | SHOULD |
| SEL-04 | Clic simple sur entité avec info-bulle des attributs principaux | MUST |
| SEL-05 | Modes : Nouvelle / Ajouter / Soustraire / Intersecter | MUST |
| SEL-06 | Compteur "N entité(s) sélectionnée(s)" en temps réel dans la barre de statut | MUST |
| SEL-07 | Boutons : Tout sélectionner / Tout désélectionner / Inverser | MUST |
| SEL-08 | Surlignage (highlight) des entités sélectionnées en jaune/orange | MUST |

---

## 5.1.3 Onglet Requête simple

| ID | Exigence | Priorité |
|---|---|---|
| RS-01 | Formulaire : couche → champ → opérateur → valeur | MUST |
| RS-02 | Opérateurs : `=` `≠` `>` `≥` `<` `≤` `CONTIENT` `COMMENCE PAR` `EST NULL` `ENTRE` | MUST |
| RS-03 | Auto-complétion des valeurs pour champs à choix fermé (lues depuis l'API) | SHOULD |
| RS-04 | Prévisualisation "N résultat(s)" avant application | MUST |
| RS-05 | Application = sélection des entités sur la carte et dans le tableau | MUST |
| RS-06 | Historique des 10 dernières requêtes | COULD |

---

## 5.1.4 Onglet Requête multicritère

| ID | Exigence | Priorité |
|---|---|---|
| RM-01 | Constructeur visuel par blocs (couche, champ, opérateur, valeur) | MUST |
| RM-02 | Combinaisons ET / OU avec parenthèses logiques | MUST |
| RM-03 | Requête spatiale : dwithin, intersects, within | SHOULD |
| RM-04 | Requête combinée attributaire + spatiale | SHOULD |
| RM-05 | Sauvegarde d'une requête sous un nom | COULD |
| RM-06 | Affichage SQL généré (lecture seule) | COULD |
| RM-07 | **Critère état général d'ouvrage** : filtre sur `etat_general` des modèles `EtatSeuil`, `EtatTronconSeguia`, `EtatBarrageRetenue`, `EtatKhettara`, `EtatForagePuits`, `EtatPriseLocale`, `EtatMurProtection`. Valeurs : `excellent`, `bon`, `moyen_bon`, `moyen`, `moyen_mauvais`, `mauvais`, `t_mauvais`. | MUST |

```python
# Exemple requête Django correspondante à RM-07
Seuil.objects.filter(
    diagnostic_etat__etat_general__in=['mauvais', 't_mauvais']
)
```

---

## 5.1.5 Onglet Symbologie

| ID | Exigence | Priorité |
|---|---|---|
| SY-01 | Mode Simple : couleur, contour, opacité, taille | MUST |
| SY-02 | Mode Catégorisé : par valeur unique, palette auto ou personnalisée | MUST |
| SY-03 | Mode Gradué : rampe couleur, 3-9 classes, méthode Jenks/Quantile/Égal | SHOULD |
| SY-04 | Prévisualisation en direct dans la légende | MUST |
| SY-05 | Bibliothèque personnelle de styles | SHOULD |
| SY-06 | Import/export style JSON | COULD |
| SY-07 | Symbologie état diagnostic : 7 niveaux → rampe verte→rouge | MUST |
| SY-08 | **Séguias — largeur proportionnelle au débit** : largeur tracé ∝ `TronconSeguia.debit` (m³/s). Plages paramétrables ex. : 1px → 0,05 m³/s, 8px → ≥ 2 m³/s. Référence = débit max des tronçons visibles. | MUST |
| SY-09 | **Séguias — couleur par nature matériau** : chaque valeur de `TronconSeguia.nature` reçoit une couleur distincte. Valeurs lues dynamiquement depuis `/carte/api/couche/troncons_seguias/champs/nature/valeurs/` — **jamais en dur dans le JS**. | MUST |

### Implémentation SY-08 (MapLibre GL JS)

```javascript
// Exemple paint rule MapLibre pour largeur proportionnelle
{
  "line-width": [
    "interpolate", ["linear"],
    ["get", "debit"],
    0.05, 1,   // 0.05 m³/s → 1px
    0.5,  3,   // 0.5  m³/s → 3px
    2.0,  8    // 2.0  m³/s → 8px
  ]
}
```

### Implémentation SY-09 (exemple, valeurs dynamiques)

```javascript
// À GÉNÉRER dynamiquement depuis l'API — ne pas coder les valeurs
const valeurs = await fetch('/carte/api/couche/troncons_seguias/champs/nature/valeurs/');
const palette = buildCategoricalPalette(valeurs); // assigne couleur par valeur
```

---

## 5.1.6 Logique de double-clic (drill-down)

Un double-clic sur une entité zoome vers les entités filles ou associées.

| Entité cliquée | Action | Couches affichées |
|---|---|---|
| **Province** | Zoom emprise province. Filtre `communes` sur `Commune.province = province.pk` | Communes filtrées |
| **Commune** | Zoom commune. Filtre `perimetres` sur `Perimetre.commune = commune.nom_fr` | Périmètres filtrés |
| **Seuil** | Zoom sur `Seuil.bassin_versant`. Affiche le polygone BV. Affiche `ReseauHydrographique` avec style par `grid_code` (épaisseur croissante) | BassinVersant + ReseauHydro |
| **Prise locale** | Même logique → `PriseLocale.bassin_versant` | BassinVersant + ReseauHydro |
| **Barrage collinaire** | Même logique → `BarrageRetenue.bassin_versant` | BassinVersant + ReseauHydro |
| **Périmètre** | Zoom périmètre. Active et filtre tous les ouvrages du périmètre (Seuil, Seguias, Barrage…) | Ouvrages du périmètre |
| **BassinVersant** | Zoom BV. Affiche réseau hydrographique interne classifié par `grid_code` | ReseauHydro dans le BV |

### Règle de style du réseau hydrographique par grid_code

```javascript
// grid_code = ordre de Strahler (plus élevé = cours d'eau principal)
{
  "line-width": ["interpolate", ["linear"], ["get", "grid_code"], 1, 1, 5, 3, 9, 6],
  "line-color": ["interpolate", ["linear"], ["get", "grid_code"],
    1, "#a8d5f5",  // petit affluent — bleu clair
    5, "#4a90d9",  // cours moyen — bleu moyen
    9, "#1a4f8a"   // cours principal — bleu foncé
  ]
}
```

### Requêtes Django correspondantes

```python
# Double-clic Province → communes
Commune.objects.filter(province=province)

# Double-clic Seuil → BV + réseau hydro
bv = seuil.bassin_versant
reseau = ReseauHydrographique.objects.filter(geometrie__within=bv.geometrie)

# Double-clic Périmètre → tous ses ouvrages
seuils = Seuil.objects.filter(perimetre=perimetre)
seguias = Seguias.objects.filter(perimetre=perimetre)
# ... (tous les types d'ouvrages)
```
