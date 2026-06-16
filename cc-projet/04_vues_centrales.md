---
section: "04"
titre: "Vues centrales et synchronisation"
version: "2.0"
date: "2026-06-04"
tags: [carte, dashboard, tableau, export, synchronisation, Esri]
---

# §5.2 — Zone centrale et §6 — Synchronisation

La zone centrale adopte un système d'onglets : **Carte | Dashboard | Tableau**.
Les 3 vues partagent `couche_active` et `selection_active` (ids Django des entités sélectionnées).

---

## 5.2.1 Onglet Carte

| ID | Exigence | Priorité |
|---|---|---|
| CA-01 | Rendu GeoJSON ou MVT via MapLibre GL JS | MUST |
| CA-02 | Fond OSM par défaut + fond neutre | SHOULD |
| CA-03 | Barre d'outils : zoom ±, zoom emprise, pan, mesure distance/surface, plein écran | MUST |
| CA-04 | Barre de statut : SRID, échelle, coordonnées curseur, nb entités sélectionnées | MUST |
| CA-05 | Mini-carte de localisation (overview) | COULD |
| CA-06 | Info-bulle sur survol : 5 attributs principaux | MUST |
| CA-07 | Popup sur clic : tous attributs + lien fiche Django `/diagnostic/<type>/<pk>/` | MUST |
| CA-08 | Légende dynamique des couches visibles | MUST |
| CA-09 | Export carte — format papier : A4, A3, A2, A1, A0 | MUST |
| CA-10 | Export carte — orientation : Portrait / Paysage | MUST |
| CA-11 | Export carte — résolution : 72 dpi (web) / 150 dpi (brouillon) / 300 dpi (impression) | MUST |
| CA-12 | Export carte — éléments : Titre, Légende, Flèche Nord, Échelle, Logo, Date | MUST |
| CA-13 | Export carte — prévisualisation layout avant export | SHOULD |
| CA-14 | Export carte — formats : PDF, PNG, SVG | MUST |
| CA-15 | **Bouton Esri basemaps** : sélecteur 3 fonds Esri distincts du bouton OSM | MUST |

### CA-15 — Détail des 3 fonds Esri

```javascript
const ESRI_BASEMAPS = {
  imagery: {
    label: "Esri Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "Esri, DigitalGlobe"
  },
  topo: {
    label: "Esri Topographique",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: "Esri"
  },
  streets: {
    label: "Esri Streets",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: "Esri"
  }
};
```

---

## 5.2.2 Onglet Dashboard

Le dashboard se recalcule automatiquement quand `selection_active` change.

| ID | Widget | Priorité |
|---|---|---|
| DB-01 | Histogramme — distribution d'un champ numérique | MUST |
| DB-02 | Camembert/Donut — répartition par valeur catégorielle | MUST |
| DB-03 | Barres groupées — comparaison d'un indicateur par catégorie | MUST |
| DB-04 | KPI — nb entités, somme, moyenne, min/max | MUST |
| DB-05 | Carte choroplèthe miniature | SHOULD |
| DB-06 | Série temporelle (si champ date disponible) | COULD |
| DB-07 | Disposition personnalisable par glisser-déposer | COULD |
| DB-08 | Clic sur segment graphique → sélectionne entités sur la carte | SHOULD |
| DB-09 | Export dashboard : PDF ou PNG | SHOULD |
| DB-10 | Export données sous-jacentes : CSV/Excel | MUST |

### Graphiques préconfigurés par couche

| Couche active | Graphiques préconfigurés |
|---|---|
| `perimetres` | Camembert statut juridique (melk/collectif/location/guich/habous) — Barres superficie totale vs irriguée par commune — KPI total bénéficiaires |
| `seuils` | Donut `etat_general` (EtatSeuil) — Histogramme `debit_mobilise` — Barres nb seuils par périmètre |
| `troncons_seguias` | Barres longueur par type (principale/secondaire/tertiaire) — KPI efficience moyenne — Donut `nature` matériaux |
| `bassins_versants` | Scatter surface vs thalweg — Barres Q crue T10/T50/T100 — KPI surface totale |
| `stations_pluvio` | Série mensuelle Sep→Août `hauteur_moyenne` — Barres Pjmax T10/T50/T100 |

> **Important** : les catégories du Donut `nature` séguias doivent être construites
> dynamiquement depuis l'API (voir règle évolutivité).

---

## 5.2.3 Onglet Tableau attributaire

| ID | Exigence | Priorité |
|---|---|---|
| TA-01 | Grille paginée : 50/100/200 lignes par page | MUST |
| TA-02 | Colonnes redimensionnables | SHOULD |
| TA-03 | Tri ascendant/descendant sur n'importe quelle colonne | MUST |
| TA-04 | Filtre rapide par colonne (valeurs lues dynamiquement depuis l'API) | SHOULD |
| TA-05 | Surlignage jaune des lignes correspondant à `selection_active` | MUST |
| TA-06 | Clic ligne → zoom + sélection entité sur la carte | MUST |
| TA-07 | Édition inline (rôle éditeur uniquement) avec validation de type | SHOULD |
| TA-08 | Pied de tableau : nb total, nb sélectionnés, stats numériques rapides | SHOULD |
| TA-09 | Export CSV avec en-têtes | MUST |
| TA-10 | Export Excel (.xlsx) | MUST |
| TA-11 | Export JSON / GeoJSON | SHOULD |
| TA-12 | Option : exporter sélection uniquement ou tout | MUST |
| TA-13 | Option : choisir colonnes à exporter | SHOULD |

---

## 6. Interactions et synchronisation entre vues

État global partagé :
- `couche_active` : détermine les champs disponibles dans requêtes, tableau, graphiques
- `selection_active` : set de `pk` Django des entités sélectionnées

| Événement | Vue source | Effet sur les autres vues |
|---|---|---|
| Sélection d'entités (outil) | Carte | Tableau : surligne lignes + scroll. Dashboard : recalcule graphiques. |
| Clic ligne tableau | Tableau | Carte : zoom + surligne. Dashboard : met à jour si applicable. |
| Clic segment graphique | Dashboard | Carte : sélectionne + surligne. Tableau : filtre sur les lignes du segment. |
| Application requête | Panneau gauche | Carte + Tableau + Dashboard : recalculent tous sur le résultat. |
| Changement couche active | Panneau gauche | Tableau : affiche attributs nouvelle couche. Dashboard : graphiques préconfigurés. |
| Résultat outil (nouvelle couche) | Panneau droit | Gestionnaire couches : ajoute couche résultat. Carte : affiche automatiquement. |
| Double-clic entité | Carte | Zoom + affichage couches filles (voir §5.1.6). |
