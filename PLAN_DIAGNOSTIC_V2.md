# Plan d'évolution — Module Diagnostic (V2)

**Date :** 2026-06-08  
**Statut :** Idéation — en attente d'implémentation

---

## Point 1 — Supprimer la logique de validation des templates

### Ce qui change
- Supprimer tous les blocs `{% if user.role == 'operateur' %}...valider/invalider...{% endif %}` dans tous les templates
- Supprimer la colonne **Statut** des tableaux (badge vert/orange) — ni bouton, ni affichage
- Supprimer les stats "Validés / Non valides" dans `perimetre_list.html` et `suivi_evaluation.html`
- Le champ `statut` reste en base de données (migrations intactes, champ `valide_par` aussi) — juste invisible dans l'UI

### Fichiers touchés
- `templates/diagnostic/ouvrages_tete/detail.html`
- `templates/diagnostic/perimetre_list.html`
- `templates/diagnostic/reseaux_irrigation/detail.html`
- `templates/diagnostic/suivi_evaluation.html`
- `templates/diagnostic/suivi/seuils.html`
- `templates/diagnostic/suivi/barrages.html`
- `templates/diagnostic/suivi/khettaras.html`
- `templates/diagnostic/suivi/forages.html`
- `templates/diagnostic/suivi/murs.html`
- `templates/diagnostic/suivi/prises.html`
- `templates/diagnostic/suivi/seguias.html`

---

## Point 2 — Un seul bouton Import SHP dans `accueil.html`

### Ce qui change
- Supprimer tous les boutons "Import .shp" dispersés dans `ouvrages_tete/detail.html` et `reseaux_irrigation/detail.html`
- Ajouter **un bouton unique** dans `accueil.html` → `/diagnostic/importer-shp/`
- Refonte complète du template `shp_import_unified.html` en wizard 3 étapes

### Étape 1 — Choix + Upload
- Sélecteur type : Seuil / Mur / Barrage / Khettara / Forage / Prise / Séguia / Périmètre
- Sélecteur périmètre existant **ou** saisir un nouveau nom de périmètre
- Upload du fichier `.zip` contenant `.shp + .dbf + .shx`
- Un seul SHP peut contenir plusieurs entités (ex : plusieurs seuils)

### Étape 2 — Aperçu structure + mapping dynamique
- Après upload, le serveur lit les colonnes du SHP et les affiche
- Tableau : `colonne SHP détectée → champ modèle` (select avec tous les champs disponibles)
- Bouton **"Structure recommandée ArcGIS"** : pré-remplit le mapping selon la table standard
- Bouton **"Mapping personnalisé"** : permet d'ajuster chaque colonne manuellement

#### Structure recommandée (table attributaire ArcGIS) par type

| Type | Colonnes SHP recommandées |
|---|---|
| Seuil | `nom`, `nature`, `type`, `materiaux`, `debit`, `longueur`, `largeur`, `hauteur` |
| Mur | `rive`, `position`, `nature_mat`, `longueur`, `hauteur` |
| Barrage | `nom`, `capacite`, `debit_der`, `longueur`, `largeur`, `hauteur` |
| Khettara | `nom`, `debit`, `longueur`, `materiaux` |
| Forage | `nom`, `debit`, `profondeur`, `diametre`, `energie` |
| Prise | `nom`, `forme`, `largeur`, `hauteur`, `diametre` |
| Séguia | `nom_seg`, `type_seg`, `nature`, `longueur`, `debit` |
| Périmètre | `ksar`, `commune`, `province`, `surf_tot`, `surf_irr`, `nb_benef` |

### Étape 3 — Confirmation + import
- Prévisualisation du nombre d'entités détectées dans le SHP
- Bouton "Importer"

### Côté vue Django
- La vue `shp_import_unified` devient un wizard 2 requêtes :
  1. POST upload → extraction SHP → stockage chemin en session → redirect vers mapping
  2. GET mapping → affichage colonnes → POST mapping → import effectif

### Fichiers touchés
- `templates/diagnostic/accueil.html` (ajout bouton)
- `templates/diagnostic/ouvrages_tete/detail.html` (suppression boutons Import .shp)
- `templates/diagnostic/reseaux_irrigation/detail.html` (suppression bouton Import .shp)
- `templates/diagnostic/shp_import_unified.html` (refonte complète)
- `diagnostic/views.py` — refonte `shp_import_unified()` en 2 étapes

---

## Point 3 — Export Excel — Fiche enquête vide (template de saisie terrain)

### Ce qui change
- Bouton **"Télécharger enquête globale"** dans `accueil.html` → `/diagnostic/export-enquete/`
- Vue `export_enquete_global` : génère un classeur Excel **vide** (aucune donnée de la base)
  servant de **fiche de saisie terrain** pour le diagnostic

### Règles de contenu
- **Aucune ligne de données** — uniquement les en-têtes (structure pour saisie manuelle)
- **Pas de champs issus de calculs ou d'analyses** : exclure
  `volume_annee_*`, `volume_excedent_deficit_*`, `et0_mm_jour`, `efficiance_reseau`,
  `efficience_calculee`, `perte_infiltration_m3s`, `perte_vaporisation_m3s`,
  `date_dernier_calcul`, `efficience_reseaux` (ouvrages)
- **Pas de champs système** : exclure `statut`, `created_at`, `updated_at`, `geometrie`
- **Inclure les tables enfants** de `Perimetre` (3 onglets dédiés)

### Structure du classeur (12 onglets)
| Onglet | Contenu |
|---|---|
| Périmètres | Identité + caractéristiques terrain (sans champs analyse) |
| Assolement | Table enfant `Assolement` (culture, %, surface, rendement) — avec colonne référence périmètre |
| Tours d'eau | Table enfant `TourEau` (ayant droit, cycle, durée) |
| Organisations | Table enfant `OrganisationAgriculteur` (nom) |
| Seuils | Champs identité + dimensions + `EtatSeuil` (critères 0-5) |
| Barrages | Identité + dimensions + critères `EtatBarrageRetenue` |
| Khettaras | Identité + dimensions + critères `EtatKhettara` |
| Forages | Identité + dimensions + critères `EtatForagePuits` |
| Murs | Identité + dimensions + critères `EtatMurProtection` |
| Prises | Identité + dimensions + critères `EtatPriseLocale` |
| Séguias | Identité séguia (sans données tronçons) |
| Tronçons séguias | Dimensions + critères `EtatTronconSeguia` (sans efficiences calculées) |

- En-têtes colorées (fond `#1a1a2e`, texte blanc)
- Largeurs de colonnes auto-ajustées
- Fichier nommé `fiche_enquete_diagnostic_YYYYMMDD.xlsx`

### Fichiers touchés
- `templates/diagnostic/accueil.html` (ajout bouton)
- `diagnostic/views.py` (nouvelle vue `export_enquete_global`)
- `diagnostic/urls.py` (nouveau pattern `export-enquete/`)

---

## Point 4 — Export Excel par périmètre

### Ce qui change
- Bouton icône Excel dans `perimetre_list.html` (colonne Actions) → `/diagnostic/perimetres/<pk>/export-excel/`
- Vue `perimetre_export_excel` : classeur Excel pour **un seul périmètre**

### Structure du classeur
| Onglet | Contenu |
|---|---|
| Périmètre | Toutes les infos (superficie, bénéficiaires, assolement, tours d'eau, organisations) |
| Seuils | Seuils du périmètre + colonnes diagnostic |
| Barrages | Idem |
| Khettaras | Idem |
| Forages | Idem |
| Murs | Idem |
| Prises | Idem |
| Séguias | Séguias + tronçons + colonnes diagnostic |

### Fichiers touchés
- `templates/diagnostic/perimetre_list.html` (ajout bouton Excel)
- `diagnostic/views.py` (nouvelle vue `perimetre_export_excel`)
- `diagnostic/urls.py` (nouveau pattern `perimetres/<pk>/export-excel/`)

---

## Point 5 — Correction des types géométriques

### Modèles à modifier dans `diagnostic/models.py`

| Modèle | Champ | Actuel | Nouveau |
|---|---|---|---|
| `Perimetre` | `geometrie` | `GeometryField` | **supprimé** (pas de géométrie) |
| `MurProtection` | `geometrie` | `GeometryField` | `PointField` |
| `BarrageRetenue` | `geometrie` | `GeometryField` | `PointField` |
| `Khettara` | `geometrie` | `GeometryField` | `PointField` |
| `ForagePuits` | `geometrie` | `GeometryField` | `PointField` |
| `PriseLocale` | `geometrie` | `GeometryField` | `PointField` |
| `TronconSeguia` | `geometrie` | `GeometryField` | `LineStringField` |
| `Seuil` | `geometrie` | `PointField` | déjà correct ✓ |

### Migration
- Créer `diagnostic/migrations/0032_fix_geometry_types.py`
- Ne jamais modifier les migrations existantes

### Fichiers touchés
- `diagnostic/models.py`
- `diagnostic/migrations/0032_fix_geometry_types.py` (généré par `makemigrations`)

---

## Point 6 — Présentation géométrique Leaflet

### Ce qui change
- Ajouter un onglet **Carte** dans `ouvrages_tete/detail.html`
- Ajouter une carte dans `reseaux_irrigation/detail.html`

### Carte dans `ouvrages_tete/detail.html`
- Fond OpenStreetMap via Leaflet
- Couche **Points** orange : tous les ouvrages du périmètre (Seuil, Mur, Barrage, Khettara, Forage, Prise)
- Couche **Lignes** bleue : tronçons Séguia (LineString)
- Popup au clic : nom + type + état diagnostic
- Style cohérent avec la carte de l'app `analyse_hydrologique`

### Carte dans `reseaux_irrigation/detail.html`
- Fond OpenStreetMap
- Couche **Lignes** bleue : tronçons séguia du périmètre uniquement
- Popup au clic : nom séguia + tronçon + état

### Données GeoJSON
- Les vues `ouvrages_tete_detail` et `reseaux_irrigation_detail` injectent les géométries en JSON dans le contexte template
- Sérialisation via `django.core.serializers.serialize('geojson', queryset)`

### Fichiers touchés
- `templates/diagnostic/ouvrages_tete/detail.html`
- `templates/diagnostic/reseaux_irrigation/detail.html`
- `diagnostic/views.py` (ajout sérialisation GeoJSON dans les vues existantes)

---

## Point 7 — Droits administrateur = droits opérateur dans Diagnostic

### Constat actuel
- Le décorateur `@operateur_requis` dans `diagnostic/views.py` autorise déjà `'administrateur'` :
  ```python
  if request.user.role not in ('operateur', 'administrateur'):
  ```
- Mais dans les **templates**, les boutons d'action (valider, supprimer) sont protégés par :
  ```django
  {% if user.role == 'operateur' %}
  ```
  → L'administrateur ne voit pas ces boutons malgré son accès côté serveur

### Ce qui change
- Remplacer **toutes les occurrences** `{% if user.role == 'operateur' %}` dans les templates diagnostic par :
  ```django
  {% if user.role == 'operateur' or user.role == 'administrateur' %}
  ```
- Cela concerne : boutons Supprimer dans `ouvrages_tete/detail.html`, `perimetre_list.html`, `reseaux_irrigation/detail.html`
- Note : cette modification est à combiner avec le **Point 1** (suppression validation) — au final, seul le bouton Supprimer restera dans ce bloc conditionnel

### Fichiers touchés
- `templates/diagnostic/ouvrages_tete/detail.html`
- `templates/diagnostic/perimetre_list.html`
- `templates/diagnostic/reseaux_irrigation/detail.html`
- `templates/diagnostic/suivi/*.html` (si des actions y existent)

---

## Point 8 — Saisie géométrique dans les formulaires d'ouvrages

### Contexte
Chaque formulaire de création/modification d'un ouvrage doit permettre à l'utilisateur
de renseigner la géométrie de l'entité via **3 méthodes au choix**, selon le type de géométrie.

> **Les boutons "Import .shp" individuels présents dans les entêtes de tableaux
> (image ci-dessus) sont supprimés** — l'import SHP se fait uniquement depuis
> le bouton unique de l'accueil (Point 2).

---

### Géométrie Point — Seuil, Mur, Barrage, Khettara, Forage, Prise

#### Méthode 1 — Saisie manuelle de coordonnées
- Deux champs numériques dans le formulaire :
  - **Coordonnée X** (Est, en mètres, système Nord Maroc EPSG:26191)
  - **Coordonnée Y** (Nord, en mètres, système Nord Maroc EPSG:26191)
- Les champs `coordonnes_x` / `coordonnes_y` existent déjà sur `Seuil`
  → Étendre le même pattern aux autres ouvrages si absent
- Conversion automatique EPSG:26191 → EPSG:4326 (WGS84) avant stockage dans `geometrie`

#### Méthode 2 — Clic sur carte Leaflet (dans le formulaire)
- Petite carte Leaflet intégrée dans le formulaire (fond OpenStreetMap)
- L'utilisateur clique sur la position de l'ouvrage
- Le clic met à jour automatiquement les champs X/Y (affichés en Nord Maroc mètres)
- Un marqueur orange confirme la position choisie
- Centrage initial sur la région Tafilalet/Midelt

#### Méthode 3 — Depuis le SHP unifié (Point 2)
- Pas de bouton dans le formulaire individuel
- L'utilisateur passe par `accueil → Importer SHP` pour créer des entités en masse depuis un fichier SHP

---

### Géométrie LineString — TronconSeguia

#### Méthode 1 — Saisie d'une liste de points
- Tableau dynamique dans le formulaire : liste de paires (X, Y) en Nord Maroc mètres
- Boutons + / − pour ajouter/retirer des points du tracé
- Conversion automatique liste de points EPSG:26191 → LineString EPSG:4326

#### Méthode 2 — Tracé sur carte Leaflet (dans le formulaire)
- Carte Leaflet avec outil de dessin Polyline (plugin Leaflet.draw)
- L'utilisateur trace le tronçon point par point
- Le tracé est converti en liste de coordonnées (affichée dans le tableau de points ci-dessus)
- Un tracé bleu confirme la géométrie

#### Méthode 3 — Depuis le SHP unifié (Point 2)
- Idem que pour les points

---

### Interface dans les formulaires

```
┌─────────────────────────────────────────────────────┐
│  Géométrie de l'ouvrage                             │
│  ─────────────────────────────────────────────────  │
│  [●] Saisir les coordonnées   [●] Clic sur la carte │
│                                                     │
│  ▼ Coordonnées (Nord Maroc, m)                      │
│  X (Est) : [___________]                            │
│  Y (Nord): [___________]                            │
│                                                     │
│  ┌──────────────────────────────────┐               │
│  │         Carte Leaflet            │               │
│  │   (clic = pointe l'ouvrage)      │               │
│  │                                  │               │
│  └──────────────────────────────────┘               │
└─────────────────────────────────────────────────────┘
```

---

### Côté code

- **Formulaires** (`diagnostic/forms.py`) : ajouter champs `coord_x` / `coord_y` sur les formulaires
  manquants (Mur, Barrage, Khettara, Forage, Prise)
- **Vues `*_create` / `*_edit`** : après `form.is_valid()`, si `coord_x` et `coord_y` fournis,
  construire la `geometrie` via `Point(x, y, srid=26191).transform(4326)`
- **Templates formulaires** (`ouvrages_tete/*_form.html`) : section géométrie avec carte Leaflet
  + champs X/Y + JS de synchronisation
- **Leaflet.draw** : inclus via CDN pour le tracé des tronçons séguia

### Fichiers touchés
- `diagnostic/forms.py` (ajout champs coord_x/y sur formulaires manquants)
- `diagnostic/views.py` (construction géométrie dans les vues create/edit)
- `templates/diagnostic/ouvrages_tete/seuil_form.html`
- `templates/diagnostic/ouvrages_tete/mur_form.html`
- `templates/diagnostic/ouvrages_tete/barrage_form.html`
- `templates/diagnostic/ouvrages_tete/khettara_form.html`
- `templates/diagnostic/ouvrages_tete/forage_form.html`
- `templates/diagnostic/ouvrages_tete/prise_form.html`
- `templates/diagnostic/reseaux_irrigation/troncon_form.html`

---

## Résumé des fichiers impactés

| Fichier | Points |
|---|---|
| `diagnostic/models.py` | 5 |
| `diagnostic/migrations/0032_*.py` | 5 |
| `diagnostic/forms.py` | 8 |
| `diagnostic/views.py` | 2, 3, 4, 6, 8 |
| `diagnostic/urls.py` | 3, 4 |
| `templates/diagnostic/accueil.html` | 2, 3 |
| `templates/diagnostic/perimetre_list.html` | 1, 4, 7 |
| `templates/diagnostic/shp_import_unified.html` | 2 |
| `templates/diagnostic/ouvrages_tete/detail.html` | 1, 2, 6, 7 |
| `templates/diagnostic/ouvrages_tete/*_form.html` (×6) | 8 |
| `templates/diagnostic/reseaux_irrigation/detail.html` | 1, 2, 6, 7 |
| `templates/diagnostic/reseaux_irrigation/troncon_form.html` | 8 |
| `templates/diagnostic/suivi_evaluation.html` | 1 |
| `templates/diagnostic/suivi/*.html` (×7) | 1, 7 |

---

## Ordre d'implémentation recommandé

1. **Point 7** — Droits administrateur (1 remplacement dans 3 fichiers, risque zéro)
2. **Point 1** — Suppression validation + statut (templates uniquement, pas de migration)
3. **Point 5** — Types géométriques (migration, à faire avant Points 6 et 8)
4. **Point 8** — Saisie géométrique dans formulaires (dépend de Point 5 pour les types)
5. **Point 3 + 4** — Exports Excel (nouvelles vues, indépendantes)
6. **Point 2** — Import SHP unifié avec mapping dynamique (le plus complexe)
7. **Point 6** — Carte Leaflet résultats (dépend de Point 5)
