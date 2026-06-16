# Outil « Besoin » — Box « Outils périmètre » (panneau droit de la Carte)

Documentation fonctionnelle et technique de l'outil **Besoin**, accessible depuis
le panneau droit **Outils** de la carte SIG (`/carte/`), dans la box
**Outils périmètre**.

---

## 1. Objectif

Représenter sur la carte le **volume de besoin en eau** des périmètres irrigués,
pour une **année de référence** au choix (humide / normale / sèche), selon
plusieurs **modes de présentation** (points classés, cercles proportionnels,
diagramme circulaire, diagramme en barres, aplat de couleur).

Les valeurs ne sont **pas calculées** par l'outil : elles sont **lues telles
quelles** dans la base de données (champs `volume_annee_*` du modèle
`diagnostic.Perimetre`). L'outil est purement un **module de visualisation
thématique**.

---

## 2. Emplacement dans l'interface

```
Panneau droit « Outils »
└── Box « Outils périmètre »  (accordéon, chevron repliable)
    └── Outil « Besoin »      → ouvre un sous-panneau dédié
```

Le clic sur **Besoin** masque la liste des outils et affiche le sous-panneau
(même logique de navigation que la symbologie du panneau gauche : bouton
**← retour** pour revenir).

---

## 3. Champs du sous-panneau

| Champ | Type | Comportement |
|---|---|---|
| **Périmètres sélectionnés** | Lecture seule | Rempli automatiquement à chaque sélection sur la carte. Affiche « N périmètre(s) sélectionné(s) » ou « 0 — toute la couche » si rien n'est sélectionné. |
| **Année** | Liste | `Année normale` (défaut) · `Année humide` · `Année sèche`. |
| **Mode de présentation sur carte** | Liste | 5 modes (voir §5). |
| **Exécuter** | Bouton | Lance le rendu sur la carte. |
| **Effacer de la carte** | Bouton | Retire le résultat (marqueurs + recoloration). Apparaît après une exécution. |
| **Résultat / Légende** | Zone | Message de statut + légende contextuelle au mode choisi. |

### Compteur de sélection

Le compteur lit `window.selection_par_couche.perimetres`, exposé par
`selection.js`. Cette ventilation par couche est alimentée par les trois modes de
sélection (clic, rectangle, requête), ce qui garantit que seuls les **périmètres**
sont comptés, indépendamment de la couche active.

- **Avec sélection** → le rendu ne porte que sur les périmètres sélectionnés.
- **Sans sélection** → le rendu porte sur **toute la couche** des périmètres.

---

## 4. Source des données

- Modèle : `diagnostic.Perimetre`
- Champs (ajoutés en **migration 0031**, juin 2026) :
  - `volume_annee_humide`
  - `volume_annee_normale`
  - `volume_annee_seche`
- Géométrie : `geometrie` (SRID 4326).

Un périmètre n'apparaît que s'il possède une **valeur non nulle** pour l'année
demandée **et** une géométrie. Les périmètres sans valeur sont ignorés (signalés
dans le message de résultat).

### Positionnement des symboles

Les symboles ponctuels (points, camemberts, barres, étiquettes) sont posés au
**`point_on_surface`** de chaque polygone — un point **garanti à l'intérieur** du
périmètre (contrairement au centroïde, qui peut tomber dehors sur une forme
concave). Le calcul est fait côté serveur (GeoDjango), reprojeté en 4326.

---

## 5. Modes de présentation

| Mode (clé) | Rendu | Valeur affichée |
|---|---|---|
| **Point selon valeur** (`point_valeur`) | Cercle **classé par quantiles** (couleur + taille graduées) | au centre du cercle |
| **Cercle proportionnel** (`cercle_prop`) | Cercle bleu, taille continue ∝ valeur (échelle racine carrée) | au centre du cercle |
| **Diagramme circulaire** (`camembert`) | **Donut** : 3 parts humide/normale/sèche ; taille ∝ total des 3 années | au centre (trou du donut) |
| **Diagramme en barres** (`barres`) | 3 barres verticales (jaune/orange/bordeaux) ; taille ∝ total | en bande d'en-tête |
| **Aplat de couleur** (`choroplethe`) | Le **polygone** est coloré par classe de valeur | étiquette au centre du polygone |

### Classification (quantiles)

Les modes `point_valeur` et `choroplethe` répartissent les valeurs en **5 classes
au maximum** par **quantiles** (effectifs ~égaux), avec dédoublonnage des bornes
quand la cardinalité est faible. Rampe de couleur faible → fort :
`vert → jaune → orange → rouge → violet`.

### Couleurs par année (camembert / barres)

- Camembert : `humide #2980b9` · `normale #27ae60` · `sèche #e67e22`
- Barres : `humide #f1c40f` · `normale #e67e22` · `sèche #8e1f3d`

### Valeur affichée

Dans **tous les modes**, la valeur affichée est celle de **l'année sélectionnée**
(`value`). Les modes camembert/barres montrent en plus la **répartition des 3
années** via les parts/barres.

Dans ces deux modes, la **part / barre de l'année sélectionnée est mise en
évidence** (contour blanc pour le camembert, contour foncé pour les barres) et
**signalée dans la légende** (anneau d'accent + badge « affichée »), pour relier
visuellement la valeur centrale à sa contribution dans la répartition.

### Légende

Chaque mode produit sa propre légende dans le sous-panneau :
- classes (quantiles) pour point/choroplèthe,
- échelle proportionnelle (min/max) pour le cercle,
- couleurs des 3 années pour camembert/barres.

---

## 6. Rendu technique

- **Symboles ponctuels** (point, cercle, camembert, barres, étiquette) :
  `maplibregl.Marker` à base d'un élément **DOM/SVG**. Choix volontaire : un
  élément HTML s'affiche **toujours au-dessus du canvas WebGL**, sans dépendre du
  z-order des couches, du serveur de glyphes ni des expressions `paint` (qui
  pouvaient échouer silencieusement avec une couche `circle`/`symbol`).
- **Choroplèthe** : recoloration de la couche WebGL `lyr-perimetres` via une
  expression `['match', ['id'], pk, couleur, …, défaut]` sur `fill-color`. La
  couleur et l'opacité d'origine sont **sauvegardées puis restaurées** au
  nettoyage. Ce mode requiert que la couche « Périmètres agricoles » soit active.
- **Cadrage** : `flyTo` sur le point unique (évite le `fitBounds` inerte d'une
  emprise dégénérée) ; `fitBounds` sur l'emprise pour plusieurs points.

---

## 7. Intégration au compositeur Layout (export PDF)

Les marqueurs étant des éléments DOM, ils ne sont pas dans le canvas WebGL et
seraient absents d'une capture brute. Pour les inclure :

1. `map.js` active **`preserveDrawingBuffer: true`** (sinon `toDataURL()` renvoie
   une image vide sur WebGL).
2. `outils-perimetre.js` expose **`window.getBesoinOverlay()`** → liste des
   symboles courants (coord, type, couleur, taille, valeur, parts…).
3. `layout.js` **composite** ces symboles par-dessus l'image capturée
   (`map.project(coord)` → pixels, gestion du `devicePixelRatio`) : cercles,
   donuts, barres et étiquettes sont redessinés. Le choroplèthe, étant en WebGL,
   est capturé **nativement**.

L'aperçu **et** le PDF final présentent donc le dernier résultat affiché.

---

## 8. API

### Endpoint

```
GET /carte/api/perimetres/besoin/?annee=<humide|normale|seche>&pks=<id,id,…>
```

| Paramètre | Obligatoire | Description |
|---|---|---|
| `annee` | non (défaut `normale`) | Année de référence. |
| `pks` | non | Restreint aux PKs fournis (sélection). Sans ce paramètre → toute la couche. |

### Réponse (FeatureCollection GeoJSON)

```json
{
  "type": "FeatureCollection",
  "annee": "normale",
  "count": 1,
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-4.80871, 32.54459] },
      "properties": {
        "pk": 8,
        "nom": "…",
        "value": 121195.0,
        "v_humide": 0.0,
        "v_normale": 121195.0,
        "v_seche": 0.0
      }
    }
  ]
}
```

- `value` : valeur de l'année demandée (modes point / cercle / choroplèthe).
- `v_humide` / `v_normale` / `v_seche` : les trois valeurs (camembert / barres).

Authentification : `@api_login_required` (`@require_GET`).

---

## 9. Fichiers concernés

| Fichier | Rôle |
|---|---|
| [carte/api_views.py](api_views.py) | Vue `perimetres_besoin_points` (point_on_surface + valeurs). |
| [carte/urls.py](urls.py) | Route `api/perimetres/besoin/`. |
| [carte/static/carte/js/outils-perimetre.js](static/carte/js/outils-perimetre.js) | Logique de l'outil : panneau, modes, marqueurs, légendes. |
| [carte/static/carte/js/selection.js](static/carte/js/selection.js) | Expose `window.selection_par_couche` (compteur fiable). |
| [carte/static/carte/js/layout.js](static/carte/js/layout.js) | Compositing des symboles à la capture. |
| [carte/static/carte/js/map.js](static/carte/js/map.js) | `preserveDrawingBuffer: true`. |
| `templates/carte/index.html` | HTML de la box, du sous-panneau, du menu de modes, CSS, câblage des scripts. |
| `diagnostic/models.py` (+ migration 0031) | Champs source `volume_annee_*`. |

---

## 10. Workflow utilisateur

1. Activer la couche **Périmètres agricoles** (panneau gauche).
2. (Optionnel) Sélectionner un ou plusieurs périmètres sur la carte.
3. Panneau droit **Outils** → **Outils périmètre** → **Besoin**.
4. Choisir l'**année** et le **mode de présentation**.
5. **Exécuter** → le résultat s'affiche sur la carte + la légende dans le panneau.
6. (Optionnel) Onglet **Layout** → **Capturer** → **Générer PDF** pour exporter.
7. **Effacer de la carte** pour nettoyer.

---

## 11. Limites connues / évolutions possibles

- Le mode **choroplèthe** nécessite que la couche périmètres soit visible.
- La valeur affichée est celle de l'**année sélectionnée** ; dans les modes
  camembert/barres, la part/barre de cette année est désormais **mise en
  évidence** (contour + repère dans la légende), en plus de la répartition des
  3 années.
- Aucune logique de **calcul** du besoin : l'outil suppose les `volume_annee_*`
  déjà renseignés en base (saisis via le module Bilan / admin).
- Pistes : méthode de classification au choix (quantiles / intervalles égaux /
  Jenks), export des points en CSV/GeoJSON, infobulle au survol des symboles.
```
