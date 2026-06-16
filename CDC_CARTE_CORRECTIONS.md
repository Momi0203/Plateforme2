# CDC — Corrections & Évolutions du Module Carte

**Date :** 2026-06-10  
**Module :** `carte/` — Plateforme SIG Tafilalet / Midelt  
**Priorité :** Corrections bloquantes + améliorations UX majeures  
**Fichiers principaux :** `carte/templates/carte/index.html`, `carte/static/carte/js/*.js`, `carte/static/carte/css/carte.css`

---

## 1. PANNEAU GAUCHE

### BUG-L1 — Désalignement du template entre les trois zones

**Problème :** La mise en page à 3 colonnes (panneau gauche | carte centrale | panneau droit) présente un désalignement visuel : les hauteurs, marges et paddings des trois zones ne sont pas homogènes. En particulier le panneau gauche est décalé visuellement par rapport aux zones centrale et droite.

**Correction :**
- Harmoniser les propriétés CSS `height`, `min-height`, `padding-top`, `padding-bottom` des trois colonnes dans `carte.css` et dans le `<style>` inline de `index.html`.
- S'assurer que les trois panneaux partagent exactement le même `flex-container` avec `align-items: stretch`.
- Vérifier que la barre de navigation du Panneau de contrôle (`#panneau-navbar`) a la même hauteur dans les trois zones.
- Tester aux trois breakpoints responsive existants (1100px, 800px, 560px).

---

### BUG-L2 — Panneaux gauche et droit non rétractables (glissement manquant)

**Problème :** Les panneaux latéraux ne se rétractent pas avec une animation de glissement (slide) lorsqu'on clique sur les boutons de bascule. Le comportement attendu ressemble à Google Earth Pro : le panneau se replie latéralement en laissant un bouton `◄`/`►` (flèche) visible sur le bord de la zone carte pour le rouvrir.

**Correction :**
- Ajouter deux boutons de bascule (`#toggle-left-panel`, `#toggle-right-panel`) positionnés en `position: absolute` sur le bord gauche et droit de la zone carte (`#map-container`).
- Chaque bouton affiche `◄` (panneau ouvert) ou `►` (panneau fermé) et s'inverse à la bascule.
- Animer le collapse avec une CSS transition : `transition: width 0.25s ease, opacity 0.2s ease` sur les panneaux.
- Largeur fermée : `0px` + `overflow: hidden`. Largeur ouverte : valeur actuelle (variable CSS `--left-panel-width`).
- Les boutons doivent rester visibles et cliquables même panneau fermé (positionnés sur le bord de la zone centrale, pas à l'intérieur du panneau).
- Persister l'état dans `localStorage` (`carte_left_open`, `carte_right_open`) pour restaurer l'état après rechargement.

**Exemple CSS sketch :**
```css
#panneau-gauche {
  width: var(--left-panel-width, 320px);
  overflow: hidden;
  transition: width 0.25s ease;
}
#panneau-gauche.collapsed { width: 0; }
#toggle-left-panel {
  position: absolute;
  left: var(--left-panel-width, 320px);
  top: 50%;
  z-index: 200;
  transition: left 0.25s ease;
}
```

---

### BUG-L3 — Libellé et icône dans la barre du Panneau de contrôle

**Problème :** La barre de titre « Panneau de contrôle » affiche un nom textuel encombrant et l'icône associée à l'onglet Requête n'est pas représentative (utilise une icône générique alors que la requête mérite une icône de filtre/entonnoir).

**Corrections :**
1. **Supprimer le libellé textuel** « Panneau de contrôle » de la barre supérieure du panneau gauche. Conserver uniquement les icônes des onglets (Couches, Sélection, Requête, Multi).
2. **Remplacer l'icône Requête** (`fa-search` ou similaire) par `fa-filter` (entonnoir), cohérent avec la notion de filtrage attributaire.
3. **Remplacer l'icône Multi-critères** par `fa-sliders-h` (curseurs), distinct du filtre simple.
4. Ajouter un `title` tooltip HTML sur chaque bouton d'onglet pour compenser l'absence de libellé.

---

### BUG-L4 — Requêtes bloquées sur couche inactive + outils couche manquants

**Problème A — Requête sur couche inactive :** Les onglets Requête et Multi-critères ne permettent d'interroger que la couche active (visible sur la carte). Si une couche est cochée dans la liste mais non chargée, ou non active, la requête échoue silencieusement.

**Correction A :**
- Dans `query.js` et `multiquery.js`, lors de la soumission, si la couche cible n'est pas encore chargée dans MapLibre (`!window.LOADED_LAYERS[couche]`), appeler `loadLayer(couche)` avant d'exécuter la requête.
- La requête POST `/carte/api/requete/simple/` et `/carte/api/requete/multicritere/` fonctionnent déjà côté serveur sans dépendance à l'état de la carte — il suffit de ne pas bloquer côté client.
- Afficher un indicateur de chargement pendant ce cas.

**Problème B — Outils manquants sur chaque couche :** Les entrées de la liste de couches (`#couches-liste`) n'exposent pas d'actions directes « Zoom vers la couche » ni « Afficher uniquement cette couche ».

**Correction B :** Ajouter deux boutons d'action dans chaque `.couche-item` de `layers.js` :

| Bouton | Icône | Nom affiché | Comportement |
|--------|-------|-------------|--------------|
| Zoom vers | `fa-expand-arrows-alt` | **Centrer** | Appelle `GET /carte/api/couche/<nom>/extent/` et applique `map.fitBounds(bbox, {padding: 40})` |
| Afficher seul | `fa-eye` | **Isoler** | Masque toutes les couches chargées sauf celle-ci (`map.setLayoutProperty(id, 'visibility', 'none')` sur les autres). Un second clic « Isoler » actif restaure toutes les visibilités. |

- Ces boutons apparaissent dans un menu contextuel (`...` ou icônes inline) sur chaque ligne de couche.
- L'état « isolé » est indiqué visuellement sur le bouton (couleur active) et une bannière subtile `"Vue isolée — [nom couche]"` s'affiche en bas de la carte avec un bouton `✕ Désactiver`.

---

### BUG-L5 — Symbologie polygon : contrôle de l'épaisseur de contour manquant

**Problème :** Dans `symbologie.js`, le `PAINT_PROPS.fill` définit `size: null` et `sizeLabel: null`, ce qui empêche tout contrôle de l'épaisseur du trait de contour des polygones. MapLibre GL ne supporte pas directement `fill-outline-width`, mais il est possible de simuler un contour épais en ajoutant un layer `line` dédié sur la même source.

**Correction :**
1. Dans `PAINT_PROPS.fill`, ajouter :
   ```js
   fill: {
     color:         'fill-color',
     outline:       'fill-outline-color',
     opacity:       'fill-opacity',
     size:          null,            // pas de fill-width natif
     strokeWidth:   'line-width',    // géré sur le layer ligne fantôme
     sizeLabel:     'Épaisseur contour (px)',
     sizeMax:       10,
   }
   ```
2. Lors du `loadLayer()` pour les couches de type `fill`, créer automatiquement un layer frère `lyr-${nom}-outline` de type `line` sur la même source GeoJSON, avec `line-color` = couleur de contour et `line-width` = 1 par défaut.
3. Dans `_renderPanel()` pour le mode `fill`, afficher le slider `Épaisseur contour` qui met à jour `map.setPaintProperty(`lyr-${nom}-outline`, 'line-width', val)`.
4. La visibilité du layer outline suit la visibilité du layer fill (synchroniser dans `layers.js` lors des toggles de visibilité).

---

### BUG-L6 — Mode Catégorisé de la symbologie non fonctionnel

**Problème :** Le mode « Catégorisé » (SY-02) dans `symbologie.js` ne fonctionne pas : après sélection du champ de classification et clic « Appliquer », la carte ne se met pas à jour avec les couleurs par valeur.

**Diagnostic attendu** (à vérifier à l'implémentation) :
- L'appel à `GET /carte/api/couche/<nom>/champs/<champ>/valeurs/` retourne-t-il les valeurs uniques correctement ?
- La construction de l'expression MapLibre `['match', ['get', champ], val1, color1, ..., fallback]` est-elle correctement formée ?
- `map.setPaintProperty()` est-il appelé sur la bonne propriété selon le `_ltype` ?

**Correction :**
1. Vérifier et corriger la construction de l'expression `match` dans la fonction d'application catégorisée.
2. S'assurer que les valeurs `null` ou vides dans les données ont un fallback color (`'#cccccc'`).
3. Ajouter un bouton « Réinitialiser » qui repasse au style simple (couleur par défaut du groupe).
4. Afficher un message d'avertissement si le champ sélectionné a plus de 20 valeurs uniques (`"Trop de catégories (N) — affichage limité aux 20 premières"`).
5. Tester sur : `communes.type_commune`, `perimetres.statut`, `seuils.type_du_seuil`.

---

### FEATURE-L7 — Couches BassinVersant et ReseauHydrographique : état actuel et architecture duale

#### Situation constatée (2026-06-10)

Les nouveaux modèles cartographiques sont **déjà créés** dans l'app `carte` via la migration `0005_bassinversant_reseauhydrographique.py`. Le `LAYER_REGISTRY` pointe déjà vers eux. Aucune action de création de modèle n'est nécessaire.

#### Architecture duale — deux modèles distincts, deux rôles différents

| | `carte.BassinVersant` | `analyse_hydrologique.BassinVersant` |
|---|---|---|
| **Rôle** | Couche cartographique (affichage) | Entité de calcul hydrologique |
| **Champs clés** | `nom`, `superficie_km2`, `altitude_min/max/exutoire`, `thalweg_km`, `precipitations_annuelles_mm`, `geometrie` | `nom`, `surface`, `z_min/z_max`, `thalweg`, `x_exutoire`, `y_exutoire`, `ouvrage_en_tete`, `geometrie` |
| **FK entrant** | Aucun (couche de référence) | `Seuil.bassin_versant`, `PriseLocale.bassin_versant`, `BarrageRetenue.bassin_versant` |
| **Utilisé par** | `LAYER_REGISTRY`, carte MapLibre | `calculs.py`, vues `analyse_hydrologique` |
| **Action** | Conserver, compléter les données | **NE PAS supprimer** — FK actives |

| | `carte.ReseauHydrographique` | `analyse_hydrologique.ReseauHydrographique` |
|---|---|---|
| **Rôle** | Tronçons pour affichage simple | Réseau avec ordre de Strahler + `grid_code` pour drill-down |
| **Champs clés** | `bassin_versant` (FK → `carte.BV`), `comid`, `sorder`, `geometrie` | `grid_code`, `sorder`, `geometrie` (pas de FK BV depuis migration 0008) |
| **Action** | Conserver pour affichage cartographique | Conserver pour le drill-down seuil dans `drilldown.js` |

#### Actions restantes

1. **`layers.py`** — Les entrées `bassins_versants` et `reseau_hydrographique` pointent déjà sur `carte.*`. Aucune modification de droits requise : toutes les couches sont accessibles à tous les utilisateurs connectés (cf. §5 — Matrice des droits).

2. **`dashboard.js`** — Retirer l'entrée `bassins_versants` de `DB_PRECONFIG` (déjà planifié dans BUG-C3). Conserver si les données sont effectivement importées.

3. **`drilldown.js`** — Le drill-down `Seuil → ReseauHydrographique by grid_code` utilise `analyse_hydrologique.ReseauHydrographique` (avec `grid_code`). Ce chemin est indépendant du `LAYER_REGISTRY`. Le conserver tel quel — il n'y a pas de conflit.

4. **Saisie des données** — Les couches `carte.BassinVersant` et `carte.ReseauHydrographique` sont vides à ce stade. Elles doivent être alimentées via import SHP (ajouter des vues `upload_shp` dans `carte/views.py` ou via l'admin Django) pour être utiles à la carte.

5. **Relation outils Analyse ↔ BV** — Les outils S-2, S-3 (seuil → BV), PL-2, PL-3, B-2, B-3 dans le panneau droit (§3) doivent utiliser `analyse_hydrologique.BassinVersant` via les FK existantes (`seuil.bassin_versant`, etc.) — **pas** `carte.BassinVersant`. Ces deux modèles ne doivent pas être confondus dans les endpoints API.

---

## 2. ZONE CENTRALE

### BUG-C1 — Désordre textuel dans le sélecteur de fond de carte

**Problème :** L'interface de sélection de fond de carte (basemap switcher, `basemap.js`) affiche des libellés incohérents ou mal formatés : espaces superflus, noms techniques Esri non traduits, ou ordre peu intuitif pour l'utilisateur.

**Correction :**
- Standardiser les libellés dans `basemap.js` :

| Clé interne | Libellé affiché |
|-------------|-----------------|
| `satellite` | Satellite (Esri) |
| `topo` | Topographique |
| `streets` | Rues & routes |
| `osm` | OpenStreetMap |

- Supprimer tout libellé technique ou redondant du HTML rendu par le contrôle custom.
- Vérifier que le contrôle s'affiche correctement au-dessus de la carte sans débordement de texte.

---

### FEATURE-C2 — Tableau attributaire : ajouter les tables enfants de Périmètre et les ouvrages

**Problème :** L'onglet Tableau (`table.js`) affiche uniquement les attributs directs de la couche active. Pour la couche `perimetres`, les tables liées (ouvrages : seuils, séguias, murs, barrages, khettaras, forages, prises) ne sont pas accessibles depuis le tableau.

**Correction :**
1. Lorsque la couche active est `perimetres` ET qu'une ligne est sélectionnée (clic ou sélection carte), afficher un sous-panneau **« Ouvrages associés »** sous le tableau principal.
2. Ce sous-panneau contient une série d'onglets secondaires : `Seuils | Séguias | Murs | Barrages | Khettaras | Forages | Prises locales`.
3. Chaque onglet secondaire affiche un sous-tableau paginé (10 lignes) avec les attributs principaux de l'ouvrage lié au périmètre sélectionné.
4. **Endpoint API à créer :** `GET /carte/api/perimetre/<pk>/ouvrages/<type>/` qui retourne la liste JSON des ouvrages du type donné pour ce périmètre (utiliser les FK existantes dans `diagnostic`).
5. L'export CSV depuis le tableau doit pouvoir inclure les ouvrages (option `"Exporter avec les ouvrages associés"`).
6. Si aucun périmètre n'est sélectionné, le sous-panneau est masqué.

---

### BUG-C3 — Dashboard : nettoyage des graphiques et indicateurs inutiles

**Problème :** Les préconfigérations `DB_PRECONFIG` dans `dashboard.js` contiennent des graphiques et KPI qui n'apportent pas d'information utile à l'utilisateur opérationnel :

| Couche | Graphique problématique | Raison |
|--------|------------------------|--------|
| `perimetres` | `donut` sur `statut` → trop peu de catégories (2 valeurs : valide/non_valide), non représentatif | Peu informatif seul |
| `bassins_versants` | `barres` champX=`nom`, champY=`surface` | `nom` = identifiant unique → pas une catégorie |
| `troncons_seguias` | `kpi` sur `efficience_calculee` (somme) | Somme d'un ratio 0–1 = sans sens métier |
| Toutes couches | Tout graphique utilisant `nom`, `nom_fr`, `code`, `id` comme champ catégoriel X | Noms = identifiants uniques, pas des catégories |

**Correction — règles de nettoyage :**
1. **Interdire** comme `champX` catégoriel tout champ dont le nom contient `nom`, `code`, `id`, `pk`, `ref` (filtre générique).
2. **Retirer** le KPI `efficience_calculee` (somme) de `troncons_seguias` — remplacer par KPI `moyenne` de `efficience_calculee` + KPI `longueur` (somme totale).
3. **Réviser** `DB_PRECONFIG` couche par couche selon le tableau ci-dessous :

**Nouvelle `DB_PRECONFIG` recommandée :**

```js
perimetres: [
  { type: 'donut',  champ: 'commune_territoriale',  titre: 'Répartition par commune' },
  { type: 'histo',  champ: 'superficie_irriguee',   titre: 'Distribution superficie irriguée (ha)' },
  { type: 'kpi',    champs: ['nombre_beneficiaires','superficie_totale','superficie_irriguee'],
                    titre: 'Indicateurs périmètres' },
  { type: 'barres', champX: 'commune_territoriale', champY: 'nombre_beneficiaires',
                    titre: 'Bénéficiaires par commune' },
],
seuils: [
  { type: 'donut',  champ: 'etat_general',          titre: 'État général des seuils' },
  { type: 'donut',  champ: 'type_du_seuil',          titre: 'Types de seuils' },
  { type: 'histo',  champ: 'debit_mobilise',         titre: 'Distribution débit mobilisé (m³/s)' },
  { type: 'kpi',    champs: ['debit_mobilise','largeur_crete','hauteur_seuil'],
                    titre: 'Paramètres hydrauliques' },
],
troncons_seguias: [
  { type: 'donut',  champ: 'nature',                 titre: 'Nature des matériaux' },
  { type: 'donut',  champ: 'etat_general',           titre: 'État général des tronçons' },
  { type: 'histo',  champ: 'longueur',               titre: 'Distribution longueurs (m)' },
  { type: 'kpi',    champs: ['longueur'],             aggFunc: {longueur: 'sum'},
                    titre: 'Linéaire total réseau (m)' },
  { type: 'kpi',    champs: ['efficience_calculee'],  aggFunc: {efficience_calculee: 'avg'},
                    titre: 'Efficience moyenne (%)' },
],
barrages: [
  { type: 'donut',  champ: 'etat_general',           titre: 'État général des barrages' },
  { type: 'kpi',    champs: ['capacite_retenue','apport_moyen_annuel'],
                    titre: 'Capacité et apports' },
],
khettaras: [
  { type: 'donut',  champ: 'etat_general',           titre: 'État des khettaras' },
  { type: 'histo',  champ: 'debit_galerie',          titre: 'Distribution débits (m³/s)' },
],
forages_puits: [
  { type: 'donut',  champ: 'etat_general',           titre: 'État des forages' },
  { type: 'kpi',    champs: ['profondeur_forage','debit_exploitation'],
                    titre: 'Profondeur et débit' },
],
murs_protection: [
  { type: 'donut',  champ: 'etat_general',           titre: 'État des murs de protection' },
  { type: 'histo',  champ: 'longueur',               titre: 'Distribution longueurs (m)' },
],
prises_locales: [
  { type: 'donut',  champ: 'etat_general',           titre: 'État des prises locales' },
  { type: 'kpi',    champs: ['debit_derive'],         titre: 'Débit dérivé (m³/s)' },
],
stations_pluvio: [
  { type: 'kpi',    champs: ['hauteur_moyenne','pjmax_t10','pjmax_t50','pjmax_t100'],
                    titre: 'Statistiques pluviométriques' },
  { type: 'barres', champX: 'altitude', champY: 'hauteur_moyenne',
                    titre: 'Hauteur moy. vs altitude (mm)' },
],
communes: [
  { type: 'donut',  champ: 'type_commune',           titre: 'Urbain / Rural' },
  { type: 'kpi',    champs: ['population_totale','nombre_menages','superficie_km2'],
                    titre: 'Indicateurs démographiques' },
  { type: 'barres', champX: 'type_commune', champY: 'population_totale',
                    titre: 'Population par type de commune' },
],
```

4. **Règle générale à encoder dans `_buildGenericConfig()` :** Pour les couches sans `DB_PRECONFIG`, ne proposer comme champ catégoriel que les champs avec moins de 30 valeurs uniques (exclure automatiquement `nom`, `pk`, `id`, `code`).

---

### FEATURE-C4 — Onglet Layout : Compositeur de mise en page cartographique

**Problème :** L'export carte actuel (`export.js`) génère une image PNG/PDF basique sans mise en page professionnelle. L'utilisateur ne peut pas intégrer logos, titre, légende formatée, ni choisir le format papier.

**Solution proposée :** Ajouter un **4ème onglet `[Layout]`** dans la zone centrale, aux côtés des onglets existants `[Carte]`, `[Tableau]`, `[Dashboard]`. Cet onglet expose un compositeur de carte permanent (pas une modale) inspiré du Print Composer d'ArcGIS.

**Structure des onglets de la zone centrale après intégration :**

```
┌──────────────────────────────────────────────────────────┐
│   [ Carte ]   [ Tableau ]   [ Dashboard ]   [ Layout ]   │
└──────────────────────────────────────────────────────────┘
```

- `[Carte]` → vue MapLibre principale (inchangé)
- `[Tableau]` → tableau attributaire (existant)
- `[Dashboard]` → graphiques Chart.js (existant)
- `[Layout]` → compositeur de mise en page (nouveau)

L'onglet Layout est **masqué pour le rôle visiteur** (même règle que Tableau et Dashboard).

**HTML à ajouter dans `index.html` :**
```html
<li class="nav-item">
  <a class="nav-link" id="tab-central-layout-btn" data-bs-toggle="tab" href="#tab-central-layout" role="tab">
    <i class="fas fa-print"></i> Layout
  </a>
</li>
<!-- ... -->
<div class="tab-pane fade" id="tab-central-layout" role="tabpanel">
  {% include "carte/layout_composer.html" %}
</div>
```

#### C4.1 — Interface du compositeur (onglet Layout)

Le panneau du compositeur contient :

**Colonne gauche — Paramètres :**
- Sélecteur **Format papier** : `A0 | A1 | A2 | A3 | A4 | A5` (portrait et paysage)
- Sélecteur **Orientation** : Portrait / Paysage
- Sélecteur **DPI** : 96 (écran) | 150 (web) | 300 (impression)
- Champ texte **Titre de la carte** (ex. « Périmètres irrigués — Commune de Meski »)
- Champ texte **Sous-titre / description** (optionnel)
- Champ texte **Source / date** (ex. « ORMVA-TF / SGIAT — Juin 2026 »)

**Section Logos :**

> **État actuel des logos dans le projet :**
> - `static/admin/img/logo1.png` → icône 3D plateforme (sans texte)
> - `static/admin/img/logo2.png` → **HydroPlan ORMVA Tafilalet** (format pin vertical)
> - `static/admin/img/logo3.png` → **HydroPlan ORMVA Tafilalet** (format horizontal)
>
> Les logos **IAV Hassan II** et **SGIAT** ne sont **pas encore dans le projet**.
> **Action préalable** : déposer les deux fichiers dans `plateformeSIG/static/admin/img/` :
> - `logo_iav.png` — Logo IAV Hassan II (cercle vert, fourni dans les images du CDC)
> - `logo_sgiat.png` — Logo SGIAT (orange/gris, fourni dans les images du CDC)
>
> Ces noms de fichier sont utilisés dans tout le CDC ci-dessous.

| Position | Logo | Fichier statique | Statut |
|----------|------|-----------------|--------|
| Coin bas-gauche | HydroPlan (icône) | `static/admin/img/logo1.png` | ✓ Présent |
| Coin bas-centre-gauche | HydroPlan (texte) | `static/admin/img/logo2.png` | ✓ Présent |
| Coin bas-centre-droit | SGIAT | `static/admin/img/logo_sgiat.png` | ⚠ À déposer |
| Coin bas-droite | IAV Hassan II | `static/admin/img/logo_iav.png` | ⚠ À déposer |

Chaque logo a une checkbox « Inclure » (cochée par défaut) et un slider de taille (hauteur : 30–80px).

**Section Éléments cartographiques :**
- Checkbox : Inclure la **légende** (couches visibles avec couleurs)
- Checkbox : Inclure l'**échelle graphique**
- Checkbox : Inclure la **flèche nord**
- Checkbox : Inclure le **cadre de coordonnées** (grille de coordonnées)

**Colonne droite — Prévisualisation :**
- Miniature de la mise en page au format choisi (rendu HTML Canvas ou SVG)
- Le viewport de la carte actuelle est centré dans le cadre cartographique

#### C4.2 — Template de carte de référence (voir PDF fourni)

Le PDF fourni (`carte exemple de reference.pdf`) montre la mise en page cible. Points à respecter :
- Cadre extérieur avec bordure fine
- En-tête : titre de la carte + titre du projet
- Zone centrale : carte + cadre de coordonnées (X=..., Y=... en périphérie)
- Légende structurée en bas à droite avec symboles
- Bloc informations en bas à gauche : Échelle, orientation, titre court
- Logos des organisations en pied de page

#### C4.3 — Génération du PDF

**Endpoint à créer/modifier :** `POST /carte/api/export/carte/` (extension de l'existant)

Corps de la requête étendu :
```json
{
  "format": "A3",
  "orientation": "paysage",
  "dpi": 300,
  "titre": "...",
  "sous_titre": "...",
  "source": "...",
  "logos": { "hydroplan_icone": true, "hydroplan_texte": true, "sgiat": true, "iav": true },
  "elements": { "legende": true, "echelle": true, "nord": true, "grille": false },
  "map_image_base64": "...",
  "legende_items": [...]
}
```

**Backend (`api_views.py`) :** Utiliser `reportlab` (ou `weasyprint`) pour générer le PDF avec le layout structuré. Si `reportlab` n'est pas disponible, utiliser la librairie `openpyxl` (déjà présente) pour générer un PNG haute résolution et l'inclure dans une page HTML rendue en PDF via `weasyprint`.

**Logos :** Lire depuis `settings.STATICFILES_DIRS[0]` (dossier `static/`) :

```python
LOGOS = {
    'hydroplan_icone': 'admin/img/logo1.png',   # icône 3D, présent
    'hydroplan_texte': 'admin/img/logo2.png',   # logo texte HydroPlan, présent
    'sgiat':           'admin/img/logo_sgiat.png',  # à déposer
    'iav':             'admin/img/logo_iav.png',    # à déposer
}
```

Si un fichier logo est absent (non encore déposé), ignorer silencieusement ce logo dans le PDF (ne pas lever d'exception).

---

## 3. PANNEAU DROIT

### FEATURE-R1 — Restructuration complète : Analyse + Export

**Problème :** Le panneau droit actuel contient 4 onglets (Requête, Attributs, Stats, Métier) dont 3 font doublon avec le panneau gauche et le tableau central. L'onglet Métier est le seul réellement utile.

**Nouvelle structure :** Le panneau droit est divisé en **deux sections principales** accessibles via deux onglets fixes en haut du panneau :

```
[ Analyse ]  [ Export ]
```

---

### Section A — Analyse

Organisée en **boxes accordéon** par type d'entité hydraulique. Un seul box peut être ouvert à la fois. Chaque box se déroule pour exposer ses outils sous forme de sous-onglets ou de boutons d'action.

Lorsqu'un outil est activé, le résultat est affiché directement **sur la carte** (coloration des entités, popups, graphes superposés) en lien avec le zoom courant.

---

#### BOX-R-P — Périmètre irrigué

**Couche cible :** `perimetres`  
**Icône :** `fa-seedling`  
**Déclenchement :** Activé quand au moins un périmètre est sélectionné sur la carte.

| # | Nom de l'outil | Description |
|---|---------------|-------------|
| P-1 | **Évaluation des besoins en eau** | Ouvre la fiche de bilan `BilanBesoinRessources` du périmètre sélectionné. L'utilisateur choisit la station hydrométrique de référence. Lien direct vers `/bilan/<pk>/` en nouvel onglet. Si aucun bilan n'existe, lien vers la création. |
| P-2 | **Bilan volumétrique (excédents / déficits)** | Sélecteur d'année type (3 boutons : `Humide` / `Normale` / `Sèche`). Affiche sur la carte les périmètres colorés selon `volume_excedent_deficit_humide/normale/seche` (vert = excédent, rouge = déficit). Un graphique à barres en popup montre les 3 valeurs côte à côte pour le périmètre sélectionné. Zoom automatique sur le périmètre actif. |
| P-3 | **Rendement agricole global** | Calcule le rendement pondéré à partir de la table `Assolement` (culture × surface_ha × rendement). Affiche : rendement moyen pondéré (qx/ha), culture dominante, camembert de l'assolement. Endpoint : `GET /carte/api/perimetre/<pk>/rendement/` |
| P-4 | **Tours d'eau et droits d'irrigation** | Affiche la liste des `TourEau` (ayant_droit, cycle_jours, durée_heures) dans un tableau interne au panneau. Endpoint : `GET /carte/api/perimetre/<pk>/tours-eau/` |

**Champs BD utilisés (Perimetre) :**  
`volume_annee_humide/normale/seche`, `volume_excedent_deficit_humide/normale/seche`,  
`assolement` (FK → Assolement : culture, surface_ha, rendement),  
`tours_eau` (FK → TourEau : ayant_droit, cycle_jours, duree_heures)

---

#### BOX-R-S — Seuil hydraulique

**Couche cible :** `seuils`  
**Icône :** `fa-water`  
**Déclenchement :** Activé quand un seuil est sélectionné.

| # | Nom de l'outil | Description |
|---|---------------|-------------|
| S-1 | **Débit mobilisé par le seuil** | Affiche `debit_mobilise` (l/s) et les caractéristiques géométriques du seuil (longueur, hauteur, largeur_de_base) dans un encart cartographique. Calcul de la capacité nominale via la formule de déversoir. Endpoint : `GET /carte/api/couche/seuils/<pk>/` |
| S-2 | **Apport hydrologique du bassin versant** | Affiche les résultats de calcul de crue (Q10, Q100) du `BassinVersant` lié (`seuil.bassin_versant`). Navigue vers le calcul hydrologique existant via lien interne. Endpoint : `GET /carte/api/seuil/<pk>/bv-apport/` |
| S-3 | **Délimitation du bassin versant** | Zoom et mise en surbrillance du `BassinVersant` lié sur la carte. Charge temporairement la couche BV si non visible. Endpoint : `GET /carte/api/seuil/<pk>/bv/` retourne GeoJSON du BV. |
| S-4 | **Efficience du réseau alimenté** | Affiche `efficience_reseaux` (0–1) avec une jauge visuelle. Compare à l'efficience moyenne nationale de référence (0.65). Indique si des tronçons de séguia sont liés à ce seuil. |
| S-5 | **Indice de priorité d'intervention** | Voir principe détaillé §R-IP ci-dessous. Critères de `EtatSeuil` (10 critères). |

**Critères disponibles pour S-5 (`EtatSeuil`) :**

| Champ BD | Libellé |
|----------|---------|
| `etat_structurel_digue` | État structurel de la digue |
| `affouillement_aval` | Affouillement à l'aval |
| `envasement_retenue` | Envasement de la retenue |
| `murs_guideaux` | Murs guideaux |
| `radier_aval` | Radier aval |
| `etat_vannes` | État des vannes |
| `dessableur` | Dessableur |
| `degradation_beton` | Dégradation du béton |
| `infiltration_fuite` | Infiltration / fuite |
| `limiteur_debit` | Limiteur de débit |

---

#### BOX-R-PL — Prise locale

**Couche cible :** `prises_locales`  
**Icône :** `fa-faucet`  

| # | Nom de l'outil | Description |
|---|---------------|-------------|
| PL-1 | **Débit dérivé de la prise** | Affiche `debit_derive` (m³/s) et les caractéristiques du pertuis (forme, largeur_au_miroir, hauteur_pertuis). |
| PL-2 | **Apport hydrologique du bassin versant** | Identique à S-2 — utilise `prise.bassin_versant`. Endpoint : `GET /carte/api/prise/<pk>/bv-apport/` |
| PL-3 | **Délimitation du bassin versant** | Identique à S-3. Endpoint : `GET /carte/api/prise/<pk>/bv/` |
| PL-4 | **Efficience du réseau alimenté** | Affiche `efficience_reseaux`. |
| PL-5 | **Indice de priorité d'intervention** | Critères de `EtatPriseLocale` (5 critères). |

**Critères disponibles pour PL-5 (`EtatPriseLocale`) :**

| Champ BD | Libellé |
|----------|---------|
| `envasement_sedimentation_entree` | Envasement / sédimentation à l'entrée |
| `degradation_revetement` | Dégradation du revêtement |
| `accumulation_debris_vegetation` | Accumulation de débris / végétation |
| `etat_dispositifs_regulation` | État des dispositifs de régulation |
| `protection_crues_debordements` | Protection contre crues / débordements |

---

#### BOX-R-K — Khettara

**Couche cible :** `khettaras`  
**Icône :** `fa-archway`  

| # | Nom de l'outil | Description |
|---|---------------|-------------|
| K-1 | **Indice de priorité d'intervention** | Critères de `EtatKhettara` (4 critères). |

**Critères disponibles pour K-1 (`EtatKhettara`) :**

| Champ BD | Libellé |
|----------|---------|
| `envasement_ensablement_fond` | Envasement / ensablement du fond |
| `degradation_beton` | Dégradation du béton |
| `accessibilite_entretien` | Accessibilité pour l'entretien |
| `stabilite_galerie_principale` | Stabilité de la galerie principale |

---

#### BOX-R-B — Barrage collinaire / Lac de retenue

**Couche cible :** `barrages`  
**Icône :** `fa-mountain`  

| # | Nom de l'outil | Description |
|---|---------------|-------------|
| B-1 | **Apports et régime de lâchers** | Affiche les séries mensuelles (Sep→Aoû) `apports_mensuels_humide/normale/seche` issues de `BilanOuvrageAssocie`. Graphique en courbes 12 mois pour les 3 années types superposées. Également : `capacite_retenue`, `volume_attribue_irrigation`. |
| B-2 | **Apport hydrologique du bassin versant** | Identique à S-2 — utilise `barrage.bassin_versant`. Endpoint : `GET /carte/api/barrage/<pk>/bv-apport/` |
| B-3 | **Délimitation du bassin versant** | Identique à S-3. Endpoint : `GET /carte/api/barrage/<pk>/bv/` |
| B-4 | **Efficience du réseau aval** | Affiche `efficience_reseaux`. |
| B-5 | **Indice de priorité d'intervention** | Critères de `EtatBarrageRetenue` (4 critères). |

**Critères disponibles pour B-5 (`EtatBarrageRetenue`) :**

| Champ BD | Libellé |
|----------|---------|
| `affouillement_pied_digue_aval` | Affouillement au pied de digue aval |
| `taux_envasement_retenue` | Taux d'envasement de la retenue |
| `regulation_debits_aval` | Régulation des débits aval |
| `fonctionnement_ouvrages_prise_eau` | Fonctionnement des ouvrages de prise d'eau |

---

#### BOX-R-F — Forage et puits collectif

**Couche cible :** `forages_puits`  
**Icône :** `fa-tint`  

| # | Nom de l'outil | Description |
|---|---------------|-------------|
| F-1 | **Indice de priorité d'intervention** | Critères de `EtatForagePuits` (4 critères). |

**Critères disponibles pour F-1 (`EtatForagePuits`) :**

| Champ BD | Libellé |
|----------|---------|
| `qualite_physico_chimique_eau` | Qualité physico-chimique de l'eau |
| `degradation_structurelle_forage` | Dégradation structurelle du forage |
| `colmatage_forage` | Colmatage du forage |
| `etat_equipements` | État des équipements |

---

#### BOX-R-T — Tronçon de séguia

**Couche cible :** `troncons_seguias`  
**Icône :** `fa-stream`  

| # | Nom de l'outil | Description |
|---|---------------|-------------|
| T-1 | **Capacité hydraulique du tronçon (Manning)** | Appelle l'outil Manning existant (`/carte/api/outils/manning/`) avec les dimensions du tronçon sélectionné (forme, largeur_meroire, hauteur_eau, fruit_de_berge, epaisseur_parois) pré-remplies depuis la BD. L'utilisateur saisit uniquement la pente et le coefficient de Strickler manquants. Affiche Q calculé vs Q saisi (`debit`). |
| T-2 | **Rendement hydraulique du tronçon** | Affiche `efficience_calculee` (si calculé) ou `efficience_trancons` (si saisi). Calcule les pertes : `perte_infiltration_m3s`, `perte_vaporisation_m3s`. Barre de progression visuelle 0→100%. Lien vers `/efficiences/` pour recalcul complet. |
| T-3 | **Indice de priorité d'intervention** | Critères de `EtatTronconSeguia` (7 critères). |

**Critères disponibles pour T-3 (`EtatTronconSeguia`) :**

| Champ BD | Libellé |
|----------|---------|
| `fissures_revetement` | Fissures du revêtement |
| `infiltration_fuite` | Infiltration / fuite |
| `obstructions_debris` | Obstructions / débris |
| `erosion_berges` | Érosion des berges |
| `sedimentation_fond` | Sédimentation au fond |
| `ouvrages_regulation` | Ouvrages de régulation |
| `spalling_beton` | Spalling du béton |

---

#### §R-IP — Principe de l'Indice de Priorité d'Intervention (commun à tous les boxes)

Chaque box ouvrage expose un outil **"Indice de priorité d'intervention"** en deux étapes :

**Étape 1 — Calcul du score pondéré**

L'interface affiche un tableau de coefficients :

```
┌─────────────────────────────────────┬──────────────┬────────────┐
│ Critère                             │ Note (0→5)   │ Coefficient│
│                                     │ (depuis BD)  │ (saisie)   │
├─────────────────────────────────────┼──────────────┼────────────┤
│ Affouillement à l'aval              │     4        │   [  1  ]  │
│ Envasement de la retenue            │     3        │   [  1  ]  │
│ …                                   │     …        │   [  1  ]  │
└─────────────────────────────────────┴──────────────┴────────────┘
                        Score brut :  [Calculer]
```

- Les **notes (0–5)** sont lues depuis le modèle `Etat<X>` de l'entité sélectionnée.
- Les **coefficients** sont saisis par l'utilisateur (défaut = 1 pour tous). Plage : 0 à 5.
- **Score brut** = `Σ(note_i × coeff_i)` pour tous les critères non-null.
- **Score normalisé** (%) = `score_brut / score_max × 100`, où `score_max = Σ(5 × coeff_i)`.
- Un score élevé = forte dégradation = priorité d'intervention haute.

**Étape 2 — Classification et visualisation cartographique**

Après calcul pour **toutes les entités** de la couche active (pas uniquement la sélection), les scores normalisés sont classifiés en 5 niveaux :

| Classe | Score normalisé | Couleur carte | Libellé |
|--------|----------------|---------------|---------|
| 1 | 80 – 100 % | `#c0392b` rouge foncé | Intervention urgente |
| 2 | 60 – 80 % | `#e67e22` orange | Priorité haute |
| 3 | 40 – 60 % | `#f1c40f` jaune | Priorité modérée |
| 4 | 20 – 40 % | `#2ecc71` vert clair | À surveiller |
| 5 | 0 – 20 % | `#27ae60` vert foncé | Bon état |

La carte est mise à jour avec une expression MapLibre `match` sur un champ virtuel `_indice_priorite_classe` injecté dans les propriétés GeoJSON. Une légende dédiée s'affiche en bas à gauche de la carte pendant l'activation de l'outil.

Un bouton **"Réinitialiser"** restaure le style d'origine de la couche.

**Endpoint :** `POST /carte/api/outils/indice-priorite/`

Corps :
```json
{
  "couche": "seuils",
  "coefficients": {
    "affouillement_aval": 2,
    "envasement_retenue": 1,
    "etat_vannes": 3,
    "…": 1
  }
}
```

Réponse :
```json
{
  "scores": { "<pk>": 72.4, "<pk2>": 31.0, "…": "…" },
  "classes": { "<pk>": 2, "<pk2>": 4, "…": "…" },
  "max_possible": 50,
  "paint_expression": ["match", ["get", "_cls"], 1, "#c0392b", 2, "#e67e22", "…", "#27ae60"]
}
```

Le backend lit les champs de `Etat<X>` via la relation `diagnostic_etat` pour chaque entité de la couche, calcule les scores et retourne les classes. Les entités sans `Etat<X>` associé reçoivent la classe `null` (couleur grise `#95a5a6`).

---

### Section B — Export (panneau droit, onglet droit)

Zone simplifiée pour déclencher les exports courants sans quitter la vue carte.

| Bouton | Icône | Action |
|--------|-------|--------|
| **Mise en page** | `fa-print` | Bascule vers l'onglet `[Layout]` de la zone centrale : `$('#tab-central-layout-btn').tab('show')` |
| **Exporter CSV** | `fa-file-csv` | Export CSV de la couche active (sélection ou tout) |
| **Exporter GeoJSON** | `fa-file-code` | Export GeoJSON de la couche active |
| **Exporter Excel** | `fa-file-excel` | Export .xlsx de la couche active |

Ces boutons appellent les endpoints existants `GET /carte/api/export/csv/`, `geojson/`, `excel/` avec le paramètre `couche` + éventuellement `pks` (sélection active).

> Le bouton **Mise en page** ne déclenche pas une modale — il navigue vers l'onglet Layout. Cela permet à l'utilisateur de rester dans l'environnement carte, de revenir sur la carte pour ajuster le cadrage, puis de relancer la génération PDF depuis le même onglet.

---

### Suppression des onglets actuels du panneau droit

- **Requête** → déjà dans panneau gauche → supprimer.
- **Attributs** → intégré dans les popups carte (SEL-04 existant) → supprimer.
- **Stats** → intégré dans le Dashboard central → supprimer.
- **Métier** → ses outils sont distribués dans les boxes Analyse ci-dessus → supprimer le conteneur mais conserver la logique JS dans `tools.js`.

---

### FEATURE-R2 — Nouveaux endpoints API requis pour la section Analyse

**Endpoints à créer dans `carte/api_views.py` :**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `GET /carte/api/perimetre/<pk>/rendement/` | GET | Lit `Assolement`, calcule rendement pondéré = Σ(surface_ha × rendement) / Σ(surface_ha) |
| `GET /carte/api/perimetre/<pk>/tours-eau/` | GET | Retourne liste TourEau : ayant_droit, cycle_jours, duree_heures |
| `GET /carte/api/perimetre/<pk>/volume-bilan/` | GET | Retourne les 6 champs volume_* du Périmètre directement |
| `GET /carte/api/seuil/<pk>/bv/` | GET | GeoJSON du BassinVersant lié (seuil.bassin_versant) |
| `GET /carte/api/seuil/<pk>/bv-apport/` | GET | Paramètres hydrologiques du BV (surface, thalweg, Q10, Q100) |
| `GET /carte/api/prise/<pk>/bv/` | GET | GeoJSON du BV lié à PriseLocale |
| `GET /carte/api/prise/<pk>/bv-apport/` | GET | Paramètres hydrologiques du BV de la prise |
| `GET /carte/api/barrage/<pk>/bv/` | GET | GeoJSON du BV lié à BarrageRetenue |
| `GET /carte/api/barrage/<pk>/bv-apport/` | GET | Paramètres hydrologiques du BV du barrage + apports mensuels |
| `POST /carte/api/outils/indice-priorite/` | POST | Score pondéré + classification (voir §R-IP) |

Ces endpoints s'ajoutent dans `carte/api_views.py` et sont enregistrés dans `carte/urls.py`.

---

## 4. PRIORITÉS D'IMPLÉMENTATION

| Priorité | Référence | Effort estimé |
|----------|-----------|---------------|
| 🔴 Critique | BUG-L6 — Symbologie catégorisée | 2h |
| 🔴 Critique | BUG-C3 — Nettoyage dashboard | 3h |
| 🟠 Haute | BUG-L2 — Panneaux glissants | 4h |
| 🟠 Haute | BUG-L4 — Requête sur couche inactive + boutons couche | 3h |
| 🟠 Haute | BUG-L5 — Épaisseur contour polygon | 2h |
| 🟡 Moyenne | FEATURE-R1 — Restructuration panneau droit (UI + boxes) | 6h |
| 🟡 Moyenne | FEATURE-R1/§R-IP — Indice de priorité d'intervention | 6h |
| 🟡 Moyenne | FEATURE-R2 — Endpoints API Analyse (rendement, tours-eau, BV) | 5h |
| 🟡 Moyenne | FEATURE-C4 — Compositeur de carte (mise en page + logos) | 8h |
| 🟢 Basse | BOX-R-P (P-1 à P-4 périmètre) — outils analyse carte | 4h |
| 🟢 Basse | BOX-R-S/PL/B (S-1→S-4, PL-1→4, B-1→4) — apports & BV | 5h |
| 🟢 Basse | BOX-R-T (T-1 Manning, T-2 efficience) — séguias | 3h |
| 🟢 Basse | BUG-L1 — Alignement template | 1h |
| 🟢 Basse | BUG-L3 — Icônes barre panneau gauche | 1h |
| 🟢 Basse | BUG-C1 — Libellés sélecteur fond de carte | 0.5h |
| 🟢 Basse | FEATURE-C2 — Tableaux enfants ouvrages dans tableau | 5h |
| 🟢 Basse | FEATURE-L7 — Retrait BV / réseau hydrographique | 1h |

---

## 5. MATRICE DES DROITS D'UTILISATION

### 6.1 Définition des rôles dans le contexte du module Carte

| Rôle | Profil métier | Objectif dans la carte |
|------|--------------|----------------------|
| **visiteur** | Agriculteur, élu local, partenaire externe | Accès complet à toutes les fonctions de consultation, analyse et visualisation — **seul l'export de données et de cartes est interdit** |
| **opérateur** | Technicien de terrain ORMVA, agent SIG | Identique au visiteur + **export** (CSV, Excel, GeoJSON, PDF mise en page) |
| **éditeur** | Ingénieur senior, chef de projet | Identique à l'opérateur dans le module Carte — la distinction éditeur/opérateur s'applique dans les autres modules (diagnostic, bilan) |

> **Principe unique :** Dans ce module, la seule restriction du visiteur est l'**impossibilité d'exporter** les données et les cartes. Toutes les fonctions de visualisation, analyse, requêtes, tableau, dashboard, compositeur de carte et outils géospatiaux sont accessibles à tous les rôles.

---

### 6.2 Matrice des fonctions par rôle

#### Couches et navigation

| Fonction | Visiteur | Opérateur | Éditeur |
|---------|:--------:|:---------:|:-------:|
| Voir couches administratives (provinces, communes) | ✓ | ✓ | ✓ |
| Voir couches hydrologiques (stations, BV) | ✓ | ✓ | ✓ |
| Voir couches diagnostic (seuils, séguias, barrages, etc.) | ✓ | ✓ | ✓ |
| Voir couches bilan (stations climatiques, périmètres) | ✓ | ✓ | ✓ |
| Changer le fond de carte (basemap) | ✓ | ✓ | ✓ |
| Zoom / Pan / Navigation | ✓ | ✓ | ✓ |
| Drill-down Province → Communes | ✓ | ✓ | ✓ |

#### Panneau gauche

| Fonction | Visiteur | Opérateur | Éditeur |
|---------|:--------:|:---------:|:-------:|
| Liste des couches — activer / désactiver | ✓ | ✓ | ✓ |
| Bouton Centrer (zoom to layer extent) | ✓ | ✓ | ✓ |
| Bouton Isoler (display only) | ✓ | ✓ | ✓ |
| Onglet Sélection (rectangle, clic entité) | ✓ | ✓ | ✓ |
| Onglet Requête simple | ✓ | ✓ | ✓ |
| Onglet Requête multicritère | ✓ | ✓ | ✓ |
| Sauvegarder / Supprimer une requête nommée (propre) | ✓ | ✓ | ✓ |
| Symbologie Simple / Catégorisé | ✓ | ✓ | ✓ |
| Sauvegarder un style (`StyleCouche`) | ✓ | ✓ | ✓ |

#### Zone centrale

| Fonction | Visiteur | Opérateur | Éditeur |
|---------|:--------:|:---------:|:-------:|
| Onglet Carte | ✓ | ✓ | ✓ |
| Onglet Tableau attributaire | ✓ | ✓ | ✓ |
| Onglet Dashboard | ✓ | ✓ | ✓ |
| Onglet Layout (compositeur de carte) | ✓ | ✓ | ✓ |
| **Barre Export — Exporter CSV** | ✗ | ✓ | ✓ |
| **Barre Export — Exporter Excel** | ✗ | ✓ | ✓ |
| **Barre Export — Exporter GeoJSON** | ✗ | ✓ | ✓ |
| **Layout — Générer PDF (mise en page)** | ✗ | ✓ | ✓ |

#### Panneau droit — Analyse & Export

| Fonction | Visiteur | Opérateur | Éditeur |
|---------|:--------:|:---------:|:-------:|
| BOX Périmètre (P-1 à P-4) | ✓ | ✓ | ✓ |
| BOX Seuil (S-1 à S-5) | ✓ | ✓ | ✓ |
| BOX Prise locale (PL-1 à PL-5) | ✓ | ✓ | ✓ |
| BOX Khettara (K-1) | ✓ | ✓ | ✓ |
| BOX Barrage collinaire (B-1 à B-5) | ✓ | ✓ | ✓ |
| BOX Forage et puits (F-1) | ✓ | ✓ | ✓ |
| BOX Tronçon séguia (T-1 à T-3) | ✓ | ✓ | ✓ |
| Indice de priorité — calcul + visualisation | ✓ | ✓ | ✓ |
| Outils spatiaux : Buffer, Union, Dissolve, Proximité | ✓ | ✓ | ✓ |
| **Section Export panneau droit (bouton Mise en page)** | ✗ | ✓ | ✓ |

> Les lignes en **gras** sont les seules restreintes au visiteur — toutes concernent l'export de données ou de cartes.

---

### 6.3 Implémentation — Modifications requises

#### A — Hiérarchie des rôles (constante partagée)

```python
# compte/decorators.py (existant) — compléter avec :
ROLE_HIERARCHY = {'visiteur': 0, 'operateur': 1, 'editeur': 2}

def role_level(role: str) -> int:
    return ROLE_HIERARCHY.get(role, -1)

def has_role(user, *required_roles) -> bool:
    return user.is_authenticated and user.role in required_roles
```

```python
# carte/api_views.py — constante export uniquement
_EXP = ('operateur', 'editeur')   # seuls les exports sont restreints
# Supprimer _RO si existant avec une portée plus large — remplacer par _EXP
```

---

#### B — `layers.py` : aucune modification

Toutes les couches sont visibles par tout utilisateur authentifié (visiteur inclus). `acces_minimum` non nécessaire.

---

#### C — `api_views.py` : seuls les endpoints d'export sont restreints

```python
# ── GET couches, analytiques, requêtes, outils spatiaux, indice-priorité ──────
# → @api_login_required uniquement (visiteur autorisé)
@api_login_required
@require_GET
def geojson_couche(request, nom): ...

@api_login_required
@require_POST
def requete_simple(request): ...

@api_login_required
@require_POST
def outil_buffer(request): ...

@api_login_required
@require_POST
def indice_priorite(request): ...

# ── Export données — restreint au visiteur ────────────────────────────────────
@api_login_required
@role_required(*_EXP)     # _EXP = ('operateur', 'editeur')
@require_GET
def export_csv(request): ...

@api_login_required
@role_required(*_EXP)
@require_GET
def export_excel(request): ...

@api_login_required
@role_required(*_EXP)
@require_GET
def export_geojson(request): ...

# ── Export carte (PDF mise en page) — restreint au visiteur ───────────────────
@api_login_required
@role_required(*_EXP)
@require_POST
def export_carte_pdf(request): ...
```

`liste_couches` et tous les endpoints de lecture retournent toutes les couches sans filtre de rôle.

---

#### D — Template `index.html` : injection du rôle côté client

```python
# carte/views.py
@login_required
def index(request):
    from compte.decorators import ROLE_HIERARCHY
    return render(request, 'carte/index.html', {
        'user_role':       request.user.role,
        'user_role_level': ROLE_HIERARCHY.get(request.user.role, 0),
    })
```

```html
<!-- index.html — avant les <script> -->
<script>
  window.USER_ROLE       = '{{ user_role }}';
  window.USER_ROLE_LEVEL = {{ user_role_level }};
  // 0 = visiteur, 1 = operateur, 2 = editeur
</script>
```

---

#### E — JavaScript : seul l'export est masqué pour le visiteur

```js
// access.js — helpers (chargé en premier)
'use strict';
const ROLE_LEVEL = { visiteur: 0, operateur: 1, editeur: 2 };
window.hasRole = (...roles) => roles.includes(window.USER_ROLE);
window.minRole = (min)       => (window.USER_ROLE_LEVEL ?? 0) >= (ROLE_LEVEL[min] ?? 99);
```

```js
// Masquage dans index.html / export.js — UNIQUEMENT les fonctions d'export

// ── Barre export (CSV, Excel, GeoJSON) — masquée pour visiteur ───────────────
if (!window.minRole('operateur')) {
    document.getElementById('barre-export').style.display = 'none';
}

// ── Section Export du panneau droit — masquée pour visiteur ──────────────────
if (!window.minRole('operateur')) {
    document.getElementById('panneau-droit-export').style.display = 'none';
}

// ── Bouton "Générer PDF" dans l'onglet Layout — désactivé pour visiteur ───────
if (!window.minRole('operateur')) {
    const btnPdf = document.getElementById('layout-btn-generer-pdf');
    if (btnPdf) {
        btnPdf.disabled = true;
        btnPdf.title = 'Export réservé aux opérateurs et éditeurs';
    }
}

// ── Tout le reste : AUCUN masquage ────────────────────────────────────────────
// Panneau gauche, sélection, requêtes, symbologie → visibles pour tous.
// Panneau droit (Analyse), boxes, outils spatiaux → visibles pour tous.
// Tableau, Dashboard, Layout (consultation) → visibles pour tous.
```

---

#### F — `StyleCouche` et `RequeteNommee` : restriction API

```python
# Sauvegarder / supprimer un style ou une requête → tout utilisateur connecté (visiteur inclus)
@api_login_required   # pas de role_required
@require_POST
def sauvegarder_style(request): ...

@api_login_required
@require_POST
def sauvegarder_requete_nommee(request): ...

@api_login_required
@require_POST
def supprimer_requete_nommee(request, pk):
    req = get_object_or_404(RequeteNommee, pk=pk)
    if req.utilisateur != request.user:
        return JsonResponse({'erreur': 'Vous ne pouvez supprimer que vos propres requêtes'}, status=403)
    req.delete()
    return JsonResponse({'ok': True})
```

---

### 6.4 Interface par rôle après intégration

#### Vue VISITEUR

```
┌──────────────────────────────────────────────────────────────┐
│  Panneau gauche               │  [Carte][Tableau][DB][Layout] │
│  ──────────────────────────   │  ──────────────────────────   │
│  [Couches][Sélect][Req][Multi] │  ✓ Tous les onglets visibles │
│    ✓ Toutes les couches       │                               │
│    ✓ Centrer / Isoler         │  ✗ Barre Export (masquée)     │
│    ✓ Symbologie + Styles      │                               │
│    ✓ Requêtes nommées         │  Layout : consultation ✓      │
│                               │  Layout : bouton PDF ✗        │
│  Panneau droit :              │                               │
│    ✓ Boxes Analyse (P/S/PL/K/B/F/T)                          │
│    ✓ Indice de priorité                                       │
│    ✓ Outils spatiaux                                          │
│    ✗ Section Export panneau droit (masquée)                   │
└──────────────────────────────────────────────────────────────┘
```

---

#### Vue OPÉRATEUR / ÉDITEUR

```
┌──────────────────────────────────────────────────────────────┐
│  Panneau gauche               │  [Carte][Tableau][DB][Layout] │
│  ──────────────────────────   │  ──────────────────────────   │
│  [Couches][Sélect][Req][Multi] │  ✓ Tous les onglets          │
│    ✓ Toutes les couches       │  ✓ Barre Export visible       │
│    ✓ Centrer / Isoler         │                               │
│    ✓ Symbologie + Styles      │  Layout : consultation ✓      │
│    ✓ Requêtes nommées         │  Layout : bouton PDF ✓        │
│                               │                               │
│  Panneau droit :              │                               │
│    ✓ Boxes Analyse complets                                   │
│    ✓ Outils spatiaux                                          │
│    ✓ Section Export panneau droit                             │
└──────────────────────────────────────────────────────────────┘
```

---

### 6.5 Résumé des modifications de code

| Fichier | Modification |
|---------|-------------|
| `compte/decorators.py` | Ajouter `ROLE_HIERARCHY`, `role_level()`, `has_role()` |
| `carte/layers.py` | Aucune modification |
| `carte/api_views.py` | Renommer `_RO` → `_EXP`. Appliquer `@role_required(*_EXP)` uniquement aux endpoints export (csv, excel, geojson, pdf). Retirer `@role_required` de requête/outils spatiaux/indice-priorité |
| `carte/views.py` | Passer `user_role` + `user_role_level` au contexte template |
| `carte/templates/carte/index.html` | Injecter `window.USER_ROLE` + `window.USER_ROLE_LEVEL` ; ajouter onglet `[Layout]` |
| `carte/static/carte/js/access.js` | Nouveau — helpers `hasRole()` + `minRole()` |
| `carte/static/carte/js/export.js` | Masquer `barre-export` pour visiteur (`!minRole('operateur')`) |
| `carte/static/carte/js/layout.js` | Nouveau — compositeur FEATURE-C4 ; désactiver bouton PDF pour visiteur |
| `carte/static/carte/js/panneau-droit.js` | Masquer section Export panneau droit pour visiteur uniquement |
| `carte/templates/carte/layout_composer.html` | Nouveau — template HTML du compositeur (inclus via `{% include %}`) |

---

## 6. NOTES TECHNIQUES

- **Pas de nouvelle dépendance front** sauf si indispensable. Turf.js peut être ajouté en CDN uniquement pour les mesures géodésiques si les calculs haversine manuels s'avèrent insuffisants.
- **Logos statiques :** Les fichiers `logo1.png`, `logo2.png`, `logo3.png` sont des variantes du logo HydroPlan/plateforme. Les logos IAV Hassan II (`logo_iav.png`) et SGIAT (`logo_sgiat.png`) doivent être déposés manuellement dans `plateformeSIG/static/admin/img/` avant d'implémenter FEATURE-C4. Chemins template : `{% static 'admin/img/logo1.png' %}`, `{% static 'admin/img/logo_sgiat.png' %}`, `{% static 'admin/img/logo_iav.png' %}`.
- **`reportlab` :** Vérifier la disponibilité dans le venv avant d'implémenter C4. Si absent, utiliser `weasyprint` ou générer le PDF en client-side avec `jsPDF` + `html2canvas`.
- **Calendrier hydrologique :** Les dashboards qui affichent des séries mensuelles doivent respecter l'ordre Sep→Août (`MOIS_SEP_AOU`).
- **Ne pas renommer** `Besions_Ressources`, `efficiance`, ou d'autres identifiants misspelled — migrations en place.
- **Sécurité :** Le panneau droit peut appeler des outils géospatiaux intensifs (buffer, union). Ajouter un timeout côté serveur (`GEODJANGO_TIMEOUT = 30s`) et un indicateur de chargement côté client pour éviter que l'utilisateur ne double-clique.

---

## 7. PLAN D'EXÉCUTION

### 7.1 Principes d'organisation

- **Priorité :** Corrections bloquantes d'abord (bugs qui cassent l'interface existante), puis infrastructure transversale (droits, bugs UX), puis nouvelles fonctionnalités.
- **Dépendances :** La matrice des droits (§5) est un prérequis aux fonctionnalités qui masquent des éléments. FEATURE-R2 (endpoints) est un prérequis aux boxes Analyse (FEATURE-R1).
- **Estimation :** En développement seul, en heures effectives de code (hors tests manuels).

---

### 7.2 Phase 1 — Corrections bloquantes (≈ 8h)

Ces bugs dégradent l'interface existante. À traiter en priorité absolue avant toute nouvelle fonctionnalité.

| # | Item | Fichiers principaux | Durée |
|---|------|-------------------|-------|
| 1 | **BUG-L6** — Symbologie catégorisée cassée | `symbologie.js`, `layers.js` (phantom outline layer) | 2h |
| 2 | **BUG-C3** — Nettoyage `DB_PRECONFIG` dashboard | `dashboard.js` | 2h |
| 3 | **BUG-L4-A** — Requête sur couche inactive | `query.js`, `multiquery.js` | 2h |
| 4 | **BUG-L5** — Épaisseur contour polygone manquante | `symbologie.js`, `layers.js` | 2h |

---

### 7.3 Phase 2 — Infrastructure transversale (≈ 6h)

Ces éléments sont des prérequis techniques partagés. Les développer avant les nouvelles fonctionnalités pour éviter de revenir sur le code.

| # | Item | Fichiers principaux | Durée |
|---|------|-------------------|-------|
| 5 | **§5 Droits — access.js + injection rôle** | `compte/decorators.py`, `carte/views.py`, `index.html`, `access.js` | 1h |
| 6 | **§5 Droits — masquage export dans l'interface** | `export.js`, `panneau-droit.js` | 1h |
| 7 | **§5 Droits — api_views.py : _EXP sur exports uniquement** | `api_views.py` | 1h |
| 8 | **BUG-L2** — Panneaux glissants (slide gauche + droite) | `carte.css`, `index.html`, `map.js` | 3h |

---

### 7.4 Phase 3 — Corrections UX mineures (≈ 5h)

Corrections qui améliorent l'ergonomie sans bloquer les workflows existants.

| # | Item | Fichiers principaux | Durée |
|---|------|-------------------|-------|
| 9 | **BUG-L1** — Alignement template 3 colonnes | `carte.css`, `index.html` | 1h |
| 10 | **BUG-L3** — Icônes barre panneau gauche | `index.html` (HTML + CSS icons) | 1h |
| 11 | **BUG-C1** — Libellés basemap switcher | `basemap.js` | 0.5h |
| 12 | **BUG-L4-B** — Boutons Centrer / Isoler par couche | `layers.js` | 1.5h |
| 13 | **FEATURE-L7** — Retrait ancienne couche BV de `layers.py` | `layers.py`, `dashboard.js` | 1h |

---

### 7.5 Phase 4 — Panneau droit : Analyse (≈ 18h)

Nouvelle fonctionnalité principale. Dépend de la Phase 2 (droits) et requiert la création des endpoints avant l'interface.

| # | Item | Fichiers principaux | Durée |
|---|------|-------------------|-------|
| 14 | **FEATURE-R2** — Endpoints API Analyse (rendement, tours-eau, volume-bilan, BV apport/GeoJSON) | `api_views.py`, `urls.py` | 5h |
| 15 | **FEATURE-R1** — Restructuration panneau droit (HTML + CSS 2 sections) | `index.html`, `panneau-droit.js`, `carte.css` | 3h |
| 16 | **BOX-R-P** — Boîte Périmètre (P-1 à P-4) | `panneau-droit.js` ou `analyse-perimetre.js` | 3h |
| 17 | **BOX-R-S / PL / B** — Boîtes Seuil, Prise, Barrage (apports + BV) | `analyse-seuil.js`, `analyse-prise.js`, `analyse-barrage.js` | 4h |
| 18 | **BOX-R-T** — Boîte Séguia (Manning + efficience) | `analyse-seguia.js` | 2h |
| 19 | **§R-IP** — Indice de priorité d'intervention (endpoint + UI tous ouvrages) | `api_views.py`, `indice-priorite.js` | 1h (endpoint déjà spécifié) |

---

### 7.6 Phase 5 — Zone centrale : évolutions (≈ 16h)

Nouvelles fonctionnalités de la zone centrale. Peut être développé en parallèle de la Phase 4.

| # | Item | Fichiers principaux | Durée |
|---|------|-------------------|-------|
| 20 | **FEATURE-C2** — Tableaux enfants ouvrages dans tableau | `table.js`, `api_views.py` (endpoint `/perimetre/<pk>/ouvrages/<type>/`) | 5h |
| 21 | **FEATURE-C4** — Onglet Layout + compositeur (UI) | `layout.js`, `layout_composer.html`, `index.html` | 5h |
| 22 | **FEATURE-C4** — Génération PDF backend (reportlab/weasyprint) | `api_views.py` (endpoint `export_carte_pdf`) | 3h |
| 23 | **FEATURE-C4** — Logos : dépôt `logo_iav.png` + `logo_sgiat.png` | `static/admin/img/` (action manuelle préalable) | 0h |
| 24 | **BOX-R-K / F** — Boîtes Khettara + Forage (indice seulement) | `analyse-khettara.js`, `analyse-forage.js` | 3h |

---

### 7.7 Récapitulatif des phases

| Phase | Contenu | Durée estimée | Prérequis |
|-------|---------|:-------------:|-----------|
| **1** | Corrections bloquantes | 8h | — |
| **2** | Infrastructure droits + panneaux glissants | 6h | Phase 1 |
| **3** | Corrections UX mineures | 5h | Phase 2 |
| **4** | Panneau droit — Analyse | 18h | Phase 2 |
| **5** | Zone centrale — Layout + Tableau enfants | 16h | Phase 2 |
| **Total** | | **~53h** | |

> **Ordre recommandé :** Phases 1 → 2 → 3 en séquentiel (blocage mutuel). Phases 4 et 5 peuvent être développées en parallèle après la Phase 2.

---

### 7.8 Actions manuelles préalables (hors code)

Ces actions ne nécessitent pas de développement mais bloquent certaines fonctionnalités :

| Action | Bloque | Responsable |
|--------|--------|-------------|
| Déposer `logo_iav.png` dans `static/admin/img/` | FEATURE-C4 (logo IAV dans PDF) | Chef de projet |
| Déposer `logo_sgiat.png` dans `static/admin/img/` | FEATURE-C4 (logo SGIAT dans PDF) | Chef de projet |
| Importer les shapefiles `carte.BassinVersant` et `carte.ReseauHydrographique` (via admin ou upload SHP) | Couches BV et réseau hydrographique visibles sur la carte | Agent SIG |
| Vérifier disponibilité de `reportlab` dans le venv : `python -c "import reportlab"` | FEATURE-C4 backend PDF | Développeur |
