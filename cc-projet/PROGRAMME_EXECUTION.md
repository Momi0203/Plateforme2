# Programme A → Z — Développement du module Carte
# Commandes exactes à taper dans Claude Code

> **Avant chaque session** : ouvrir VSCode dans le dossier
> `c:\Users\pc\Desktop\PFE\plateformeSIG\plateformeSIG\`

---

## ═══════════════════════════════════════════
## PHASE 0 — FONDATIONS (Semaine 1)
## ═══════════════════════════════════════════

### Étape 1 — Créer l'app Django carte/

```
Lis cc-projet/06_api_architecture.md section 10.3.
Crée la structure complète de l'app Django carte/ dans plateformeSIG/ :
- carte/models.py avec StyleCouche et RequeteNommee
- carte/layers.py avec LAYER_REGISTRY pour les 15 couches de cc-projet/02_perimetre_couches.md
- carte/urls.py avec les routes /carte/ et /carte/api/
- carte/views.py avec une vue index vide
- carte/api_views.py vide
- carte/apps.py
- carte/migrations/0001_initial.py
Ajoute 'carte' dans INSTALLED_APPS de settings.py.
Ajoute les URLs dans plateformeSIG/urls.py.
```

---

### Étape 2 — Migrations

```
Lance les migrations pour la nouvelle app carte/ :
makemigrations carte
migrate
Vérifie qu'il n'y a pas d'erreurs.
```

---

### Étape 3 — Premier endpoint API (liste des couches)

```
Lis cc-projet/06_api_architecture.md section 7.1.
Dans carte/api_views.py, implémente l'endpoint :
  GET /carte/api/couches/
qui lit LAYER_REGISTRY depuis carte/layers.py et retourne
la liste des couches avec : nom, label, geom_type, groupe, fields.
Retourne un JsonResponse.
Ajoute @login_required.
Ajoute la route dans carte/urls.py.
Teste avec : python manage.py runserver puis ouvre /carte/api/couches/
```

---

### Étape 4 — Endpoint GeoJSON d'une couche

```
Lis cc-projet/06_api_architecture.md section 7.1.
Dans carte/api_views.py, implémente l'endpoint :
  GET /carte/api/couche/<nom>/
Paramètres à gérer : bbox, limit (défaut 500), offset.
Utilise LAYER_REGISTRY pour trouver le modèle.
Utilise django.contrib.gis.serializers.geojson pour sérialiser.
Pour la couche 'seuils', join avec EtatSeuil (select_related).
Filtre bbox si fourni : geometrie__bboverlaps=Polygon.from_bbox(bbox).
Retourne GeoJSON FeatureCollection.
```

---

### Étape 5 — Page HTML avec MapLibre GL JS

```
Lis cc-projet/06_api_architecture.md section 10.1.
Crée carte/templates/carte/index.html avec :
- Layout 3 colonnes : panneau gauche 280px + zone centrale + panneau droit 280px
- Intégration MapLibre GL JS via CDN
- Carte centrée sur Midelt/Tafilalet (longitude: -4.7, latitude: 32.7, zoom: 9)
- Fond de carte OSM par défaut
- Appel fetch('/carte/api/couches/') au chargement pour lister les couches disponibles
Crée carte/static/carte/js/map.js pour l'initialisation MapLibre.
```

---

### Étape 6 — Afficher la première couche (seuils)

```
Dans carte/static/carte/js/layers.js :
- Fonction loadLayer(nomCouche) qui appelle /carte/api/couche/<nom>/
- Ajoute la couche comme source GeoJSON dans MapLibre
- Style point par défaut : cercle bleu rayon 6px
- Au chargement de la page, appelle loadLayer('seuils')
Teste : les seuils doivent apparaître sur la carte.
```

---

## ═══════════════════════════════════════════
## PHASE 1 — COUCHES ET VISUALISATION (Semaines 2-3)
## ═══════════════════════════════════════════

### Étape 7 — Gestionnaire de couches (panneau gauche)

```
Lis cc-projet/03_panneau_gauche.md section 5.1.1.
Dans le panneau gauche HTML, crée le gestionnaire de couches :
- Arborescence HTML par groupes : Administratif / Hydrologie / Diagnostic
- Case à cocher par couche (PG-02)
- Icône type géométrique point/ligne/polygone (PG-04)
- Groupes repliables avec flèche (clic sur le nom du groupe)
- Clic case à cocher → appelle map.setLayoutProperty(nom, 'visibility', 'visible'/'none')
Les couches sont lues depuis /carte/api/couches/ au chargement.
```

---

### Étape 8 — Charger toutes les 15 couches

```
Lis cc-projet/02_perimetre_couches.md section 4.
Dans carte/layers.py, complète LAYER_REGISTRY avec les 15 couches.
Dans layers.js, charge toutes les couches au démarrage mais
avec visibility: 'none' par défaut sauf 'perimetres' et 'communes'.
Style par défaut selon type géométrique :
- Point → circle, rayon 5px, couleur selon groupe
- LineString → line, épaisseur 1px
- Polygon → fill + outline
```

---

### Étape 9 — Symbologie simple (panneau gauche onglet Symbologie)

```
Lis cc-projet/03_panneau_gauche.md section 5.1.5 exigences SY-01 à SY-04.
Crée un panneau symbologie qui s'ouvre quand on clique sur une couche :
- Sélecteur mode : Simple / Catégorisé
- Mode Simple : inputs couleur, opacité, taille
- Clic Appliquer → map.setPaintProperty(nomCouche, ...)
- Prévisualisation en temps réel dans la légende (SY-04)
```

---

### Étape 10 — Symbologie séguias (largeur débit + couleur nature)

```
Lis cc-projet/03_panneau_gauche.md section 5.1.5 exigences SY-08 et SY-09.

Pour SY-08 (largeur proportionnelle au débit) :
Applique ce paint rule MapLibre sur la couche 'troncons_seguias' :
  line-width interpolate linear sur le champ 'debit' : 0.05→1px, 0.5→3px, 2.0→8px

Pour SY-09 (couleur par nature) :
1. Appelle GET /carte/api/couche/troncons_seguias/champs/nature/valeurs/
2. Génère dynamiquement un match expression MapLibre avec les valeurs retournées
3. Assigne une couleur distincte à chaque valeur
NE PAS coder les valeurs nature en dur dans le JS.

Implémente aussi l'endpoint /carte/api/couche/<nom>/champs/<champ>/valeurs/
dans carte/api_views.py (voir cc-projet/07_securite_contraintes.md section 11.3).
```

---

### Étape 11 — Fonds de carte Esri

```
Lis cc-projet/04_vues_centrales.md section CA-15.
Ajoute un bouton flottant sur la carte avec 3 options Esri :
- Esri Satellite (World_Imagery)
- Esri Topographique (World_Topo_Map)
- Esri Streets (World_Street_Map)
URLs XYZ dans cc-projet/04_vues_centrales.md.
Clic sur une option → map.setStyle() ou ajouter/remplacer la source raster.
Ce bouton est séparé du sélecteur OSM.
```

---

## ═══════════════════════════════════════════
## PHASE 2 — SÉLECTION ET REQUÊTES (Semaines 4-5)
## ═══════════════════════════════════════════

### Étape 12 — Outils de sélection

```
Lis cc-projet/03_panneau_gauche.md section 5.1.2.
Implémente les 3 outils de sélection (SEL-01, SEL-04, SEL-07) :
1. Sélection par clic sur entité (SEL-04) :
   - map.on('click', nomCouche, ...) → récupère les features cliquées
   - Affiche info-bulle avec 5 attributs principaux
   - Met à jour selection_active (array de pk)
2. Sélection rectangulaire (SEL-01) :
   - Outil dessin rectangle → map.queryRenderedFeatures(bbox)
3. Boutons Tout désélectionner / Inverser (SEL-07)
4. Surlignage jaune des entités sélectionnées (SEL-08) :
   map.setPaintProperty avec filtre sur les pk sélectionnés
5. Compteur entités sélectionnées dans la barre de statut (SEL-06)
```

---

### Étape 13 — Endpoint requête simple + onglet Requête simple

```
Lis cc-projet/03_panneau_gauche.md section 5.1.3.
Lis cc-projet/06_api_architecture.md section 7.3.

1. Dans carte/api_views.py, implémente POST /carte/api/requete/simple/
   - Reçoit {couche, champ, operateur, valeur}
   - Construit un filtre Django ORM selon l'opérateur
   - Retourne {pks: [...], count: N}
   - Opérateurs à gérer : = ≠ > ≥ < ≤ CONTIENT EST_NULL ENTRE

2. Dans le panneau gauche, crée l'onglet "Requête simple" :
   - Dropdown couche → champ → opérateur → input valeur
   - Les valeurs de champs à choix fermé en auto-complétion via /champs/<champ>/valeurs/
   - Bouton Prévisualiser (RS-04) : appelle l'API, affiche "N résultats"
   - Bouton Appliquer : met à jour selection_active + surlignage carte
```

---

### Étape 14 — Requête multicritère avec état général d'ouvrage

```
Lis cc-projet/03_panneau_gauche.md section 5.1.4.

1. Dans carte/api_views.py, implémente POST /carte/api/requete/multicritere/
   - Reçoit {couche, conditions: [{champ, operateur, valeur}, ...], logique: 'ET'|'OU'}
   - Construit Q() objects Django et les combine avec & ou |
   - Pour RM-07 (état général) : jointure sur diagnostic_etat__etat_general
     Seuil.objects.filter(diagnostic_etat__etat_general__in=[valeurs])

2. Dans le panneau gauche, crée l'onglet "Requête multicritère" :
   - Bouton "Ajouter condition" → ajoute un bloc condition
   - Sélecteur ET/OU entre conditions
   - Pour les couches avec Etat<X>, ajouter le champ "État général" dans la liste des champs
   - Bouton Exécuter
```

---

## ═══════════════════════════════════════════
## PHASE 3 — TABLEAU ET DASHBOARD (Semaines 6-7)
## ═══════════════════════════════════════════

### Étape 15 — Tableau attributaire

```
Lis cc-projet/04_vues_centrales.md section 5.2.3.
Dans l'onglet Tableau de la zone centrale, crée une grille :
1. Charge les attributs via /carte/api/couche/<nom>/?fields=* (sans géométrie)
2. Pagination 50/100/200 lignes (TA-01)
3. Tri par clic sur en-tête colonne (TA-03)
4. Surlignage jaune des lignes dont le pk est dans selection_active (TA-05)
5. Clic sur ligne → zoom et sélection sur la carte (TA-06)
6. Bouton export CSV (TA-09) : appelle POST /carte/api/export/csv/
7. Synchronisation bidirectionnelle avec la carte (voir cc-projet/04_vues_centrales.md §6)
```

---

### Étape 16 — Dashboard Chart.js

```
Lis cc-projet/04_vues_centrales.md section 5.2.2.
Dans l'onglet Dashboard, implémente 4 widgets Chart.js :
1. Donut (DB-02) : champ catégoriel, catégories depuis /champs/<champ>/valeurs/
2. Histogramme (DB-01) : champ numérique, bins automatiques
3. Barres (DB-03) : comparaison par catégorie
4. KPI (DB-04) : nombre entités, somme, moyenne

Préconfiguration automatique selon la couche active :
- couche 'seuils' → Donut sur etat_general + Histogramme debit_mobilise
- couche 'troncons_seguias' → Donut sur nature + KPI efficience moyenne
(voir table complète dans cc-projet/04_vues_centrales.md)

Les graphiques se recalculent sur selection_active quand elle change.
Clic segment graphique → mise à jour selection_active (DB-08).
```

---

### Étape 17 — Double-clic drill-down

```
Lis cc-projet/03_panneau_gauche.md section 5.1.6.
Implémente la logique de double-clic sur la carte :

1. map.on('dblclick', 'provinces', ...) :
   - Récupère l'id de la province
   - Appelle POST /carte/api/requete/simple/ {couche:'communes', champ:'province', op:'=', valeur:id}
   - Affiche seulement les communes retournées
   - Zoom sur l'emprise de la province

2. map.on('dblclick', 'seuils', ...) :
   - Récupère seuil.bassin_versant_id
   - Appelle /carte/api/couche/bassins_versants/<pk>/
   - Affiche le polygone BV
   - Appelle /carte/api/couche/reseau_hydrographique/?bbox=<bbox_du_bv>
   - Affiche le réseau avec style par grid_code (code dans cc-projet/03_panneau_gauche.md)

Même logique pour Prise locale et Barrage (champ bassin_versant).
```

---

## ═══════════════════════════════════════════
## PHASE 4 — OUTILS ET EXPORTS (Semaines 8-9)
## ═══════════════════════════════════════════

### Étape 18 — Outils génériques (tampon, intersection)

```
Lis cc-projet/06_api_architecture.md section 7.4.
Dans carte/tools.py, implémente :
1. buffer(couche, pks, distance_m) :
   - Récupère les géométries sélectionnées
   - Reprojette en EPSG:26191 pour le calcul métrique
   - Applique .buffer(distance_m) avec GDAL
   - Reprojette en SRID 4326
   - Retourne GeoJSON du résultat

2. intersection(couche1, couche2) :
   - Utilise GeoDjango : qs1.filter(geometrie__intersects=...)

Expose via POST /carte/api/outils/buffer/ et /intersection/.
Le résultat est retourné en GeoJSON et ajouté comme nouvelle couche temporaire.
```

---

### Étape 19 — Box Séguia : efficience (PI + PV) et Manning

```
Lis cc-projet/05_outils_metier.md section Box Séguia.

1. Endpoint POST /carte/api/outils/efficience/ dans carte/api_views.py :
   - Reçoit {pks: [liste de TronconSeguia.pk]}
   - Pour chaque tronçon : appelle les fonctions existantes de la plateforme
     (vérifier dans plateformeSIG/static/ ou efficiences/calculs.py)
   - Sauvegarde TronconSeguia.efficience_calculee, .perte_infiltration_m3s,
     .perte_vaporisation_m3s, .date_dernier_calcul
   - Requiert rôle opérateur ou éditeur

2. Endpoint POST /carte/api/outils/manning/ :
   - Reçoit {pks: [...], n_manning: float (optionnel)}
   - Implémente Q = (1/n) × A × R^(2/3) × S^(1/2) selon la forme du tronçon
   - Retourne tableau {pk, debit_calcule} sans écrire en base

3. Dans le panneau droit, crée la Box Séguia avec les 2 boutons.
```

---

### Étape 20 — Box Seuil : score ouvrage (indice de priorité)

```
Lis cc-projet/05_outils_metier.md section Box Seuil Outil 1.

1. Endpoint POST /carte/api/outils/scoring/ :
   - Reçoit {couche, pks, coefficients: {critere: coefficient, ...}}
   - Récupère les notes depuis le modèle EtatX correspondant à la couche
   - Calcule : score = Σ(coeff_i × note_i) / Σ(coeff_max × 5) × 100
   - Classe en N classes (Jenks ou Quantile)
   - Retourne {resultats: [{pk, score, classe}, ...]}

2. Dans le panneau droit Box Seuil :
   - Formulaire avec un slider 0-5 pour chacun des 10 critères EtatSeuil
   - Les critères sont lus depuis /carte/api/couche/seuils/champs/ (noms dynamiques)
   - Bouton "Exécuter" → appelle l'endpoint
   - Résultat : carte choroplèthe colorée + tableau de scores
```

---

### Étape 21 — Export carte PDF

```
Lis cc-projet/04_vues_centrales.md section CA-09 à CA-14.

Endpoint POST /carte/api/export/carte/ :
- Reçoit {format: 'A4', orientation: 'landscape', dpi: 300,
          elements: {titre: '...', legende: true, nord: true, echelle: true}}
- Utilise WeasyPrint ou reportlab
- Génère un PDF avec l'étendue de la carte actuelle
- Retourne le PDF en streaming (StreamingHttpResponse)

Dans la barre d'outils carte, ajoute le bouton Export :
- Formulaire : format papier A4/A3/A2/A1/A0 + orientation + résolution
- Cases à cocher : Titre / Légende / Flèche Nord / Échelle / Date
- Bouton Télécharger
```

---

### Étape 22 — Export tableau (CSV et Excel)

```
Lis cc-projet/04_vues_centrales.md section TA-09 à TA-13.

Endpoint POST /carte/api/export/csv/ et /excel/ :
- Reçoit {couche, pks (optionnel), champs (optionnel)}
- Si pks vide → exporte tout
- CSV : utilise csv.writer + StreamingHttpResponse
- Excel : utilise openpyxl (déjà installé dans le venv)

Dans le tableau, ajoute les boutons Export CSV et Export Excel.
Option : sélection uniquement ou tout (TA-12).
```

---

## ═══════════════════════════════════════════
## PHASE 5 — SÉCURITÉ ET RECETTE (Semaine 10)
## ═══════════════════════════════════════════

### Étape 23 — Décorateurs de rôles

```
Lis cc-projet/07_securite_contraintes.md section 8.2.
Dans compte/decorators.py (créer si inexistant), implémente role_required(*roles).
Applique @role_required('operateur', 'editeur') sur toutes les vues api_views.py
qui ne sont pas en lecture seule (requêtes, outils, exports).
Teste : accès à /carte/api/requete/simple/ avec un compte visiteur → doit retourner 403.
```

---

### Étape 24 — Tests

```
Lis cc-projet/08_livrables_recette.md section 12.
Dans carte/tests.py, écris les tests pour les 15 critères d'acceptation :
- CA-01 : TestCase avec client visiteur → /carte/ → vérifier template
- CA-05 : TestCase requête simple seuils statut=valide → vérifier pk retournés
- CA-12 : TestCase évolutivité → ajouter valeur dans NATURE_SEGUIA_CHOICES →
          appeler /champs/nature/valeurs/ → vérifier que la nouvelle valeur est présente
- CA-13 : TestCase accès non authentifié → /carte/api/couche/seuils/ → 403
Lance : python manage.py test carte
```

---

### Étape 25 — Vérification finale

```
Lis cc-projet/08_livrables_recette.md section 12.
Lance le serveur : python manage.py runserver
Vérifie manuellement les 15 critères d'acceptation.
Si un critère échoue, dis-moi lequel et je corrige.
```

---

## ═══════════════════════════════════════════
## GUIDE D'UTILISATION RAPIDE
## ═══════════════════════════════════════════

### Pour commencer une étape

```
Copie-colle la commande de l'étape dans Claude Code.
```

### Si Claude a besoin de plus de contexte

```
Ajoute au début : "Lis aussi cc-projet/_index.md pour le contexte général."
```

### Si une étape bloque sur un modèle Django

```
"Lis plateformeSIG/diagnostic/models.py et cc-projet/05_outils_metier.md
section Box Seuil pour implémenter le scoring."
```

### Ordre des fichiers à lire selon la tâche

| Je veux coder... | Je lis d'abord... |
|---|---|
| Une couche GeoJSON | `02_perimetre_couches.md` + `06_api_architecture.md §7.1` |
| Le panneau gauche | `03_panneau_gauche.md` |
| La carte / Esri | `04_vues_centrales.md §5.2.1` |
| Le dashboard | `04_vues_centrales.md §5.2.2` |
| Le tableau | `04_vues_centrales.md §5.2.3` |
| Un outil métier | `05_outils_metier.md` |
| Une API | `06_api_architecture.md §7` |
| Les rôles | `07_securite_contraintes.md §8` |
| Les exports | `04_vues_centrales.md` + `06_api_architecture.md §7.5` |
