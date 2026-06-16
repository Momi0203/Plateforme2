# Phase — Requêtes et sélection par couche + panneaux redimensionnables

**Date :** 12 juin 2026
**Module :** Carte (`carte/`)
**Fichiers touchés :** `templates/carte/index.html`, `carte/static/carte/js/map.js`, `query.js`, `multiquery.js`, `selection.js`

---

## 1. Objectif

Restructurer le panneau gauche de la carte : supprimer les onglets globaux
**Sélect. / Requête / Multi** et rattacher ces trois fonctions **à chaque couche
individuellement**, via des boutons d'action sur chaque ligne du gestionnaire de
couches. La requête (simple ou multicritère) devient un **filtre d'affichage** :
seules les entités correspondant aux critères restent visibles sur la carte.

En complément : les panneaux gauche et droit deviennent **redimensionnables**
par glisser-déposer.

---

## 2. Avant / Après

### Avant

- Le panneau gauche avait 4 onglets : `Couches | Sélect. | Requête | Multi`.
- Les requêtes étaient globales : l'utilisateur choisissait la couche dans une
  liste déroulante à l'intérieur de l'onglet.
- Le résultat d'une requête était une **sélection** (surlignage jaune).
- Les panneaux latéraux avaient une largeur fixe (280 px).

### Après

- **Un seul écran « Couches »** dans le panneau gauche. Les onglets ont disparu.
- Chaque ligne de couche porte **6 boutons d'action** (visibles au survol) :

| Icône | Classe | Action |
|---|---|---|
| 🎨 palette | `.couche-style-btn` | Symbologie (inchangé) |
| ▼ entonnoir | `.couche-filter-btn` | **Requête simple sur cette couche** |
| ⚙ curseurs | `.couche-multi-btn` | **Requête multicritère sur cette couche** *(nouveau)* |
| ➤ pointeur | `.couche-select-btn` | **Sélection limitée à cette couche** *(nouveau)* |
| ⛶ flèches | `.couche-center-btn` | Centrer la carte (inchangé) |
| 👁 œil | `.couche-isoler-btn` | Isoler la couche (inchangé) |

- Chaque bouton ouvre un **sous-panneau** à la place de la liste des couches,
  avec un en-tête `← Retour | <Fonction> — <Nom de la couche>`. Le bouton ←
  ramène à la liste.
- La couche est **pré-remplie et masquée** dans le formulaire (le sélecteur de
  couche n'apparaît plus : le contexte est porté par l'en-tête).
- Le clic sur un bouton **rend la couche visible** automatiquement (coche la
  case → chargement GeoJSON si nécessaire).
- Le résultat d'une requête est un **filtre carte** (voir §4), plus une sélection.
- Les panneaux latéraux se redimensionnent en tirant leur bord intérieur.

---

## 3. Navigation des sous-panneaux

`selection.js` expose désormais :

```js
window.showPgPanel(tab)   // 'couches' | 'requete' | 'multi' | 'selection'
```

- Masque `#couches-liste`, `#panneau-symbologie` et tous les `[id^="pg-tab-"]`,
  puis affiche la cible (`display:flex`).
- Les boutons `← .pg-back-btn` rappellent `showPgPanel('couches')` et lèvent le
  scope de sélection.
- La symbologie conserve son propre mécanisme d'ouverture/fermeture
  (`openSymbologie` / `closeSymbologie`) — compatible car `showPgPanel` masque
  aussi son panneau.

---

## 4. Requête = filtre des entités affichées

**Principe :** la requête ne met plus en évidence les entités — elle **masque
celles qui ne correspondent pas**. Implémentation par `MAP.setFilter` MapLibre
sur l'id top-level des features (= pk Django), même idiome que le masque du
menu contextuel (`contextmenu.js`) :

```js
MAP.setFilter(`lyr-${couche}`, ['in', ['id'], ['literal', pks]]);
// + le layer fantôme `-outline` pour les polygones
```

Helpers globaux (définis dans `query.js`, partagés avec `multiquery.js`) :

```js
window.applyLayerFilter(couche, pks)  // pose le filtre + registre FILTERED_LAYERS
window.clearLayerFilter(couche)       // setFilter(null) → tout réafficher
window.FILTERED_LAYERS                // Set des couches actuellement filtrées
```

### Sous-panneau Requête simple (entonnoir)

Cascade inchangée : Champ → Opérateur (10 opérateurs RS-02) → Valeur (avec
autocomplete RS-03 si le champ a des valeurs closes).

**Conditions multiples combinées ET/OU** : le bouton **« + Ajouter une
condition »** ajoute des blocs (champ / opérateur / valeur, avec le même
autocomplete) sous la condition principale. Dès qu'il y a ≥ 2 conditions, la
barre **« Combiner les conditions » ET / OU** apparaît ; les séparateurs entre
blocs affichent la logique choisie et se mettent à jour en direct. Chaque bloc
est supprimable (✕). Toute modification d'un critère invalide la
prévisualisation (le bouton Filtrer se désactive jusqu'à la prochaine
prévisualisation).

- **Prévisualiser** → 1 condition : `POST /carte/api/requete/simple/` ;
  ≥ 2 conditions : `POST /carte/api/requete/multicritere/` avec la logique
  ET/OU. Bandeau : *« N résultats (k conditions, ET) »*.
- **Filtrer** (ex-« Appliquer ») → charge la couche si besoin puis
  `applyLayerFilter`. Bandeau : *« Filtre appliqué — N entités affichées »*.
- **Réinitialiser le filtre** (nouveau bouton) → `clearLayerFilter` ; activé
  uniquement si la couche courante figure dans `FILTERED_LAYERS`.

### Sous-panneau Multicritère (curseurs)

Constructeur de conditions inchangé (blocs dynamiques, logique ET/OU,
critère `etat_general` pour les couches avec diagnostic).

- **Filtrer** (ex-« Exécuter ») → `POST /carte/api/requete/multicritere/` puis
  `applyLayerFilter` sur les pks retournés.
- **Réinitialiser le filtre** → même comportement que la requête simple.

---

## 5. Sélection par couche (scope)

Le bouton ➤ d'une ligne couche ouvre le sous-panneau Sélection **limité à cette
couche** :

```js
window.SELECTION_SCOPE = nom;   // null = toutes les couches
```

Tant que le scope est posé, le clic sur entité, la sélection rectangulaire et
« Inverser la sélection » n'interrogent que `lyr-<couche>` (filtrage des
`layerIds` passés à `queryRenderedFeatures`). Le bouton ← retour remet le scope
à `null` (comportement global restauré).

Les outils du panneau sont inchangés : Rectangle, Tout désélectionner,
Inverser, surlignage jaune, compteur de la barre de statut.

---

## 6. Panneaux redimensionnables

Deux poignées verticales de 6 px (`.panel-resize-handle`) sont insérées entre
les panneaux et la zone centrale :

- `#resize-handle-left` — bord droit du panneau Couches ;
- `#resize-handle-right` — bord gauche du panneau Outils.

Comportement (script inline `initPanelResize` dans `index.html`) :

- glisser = largeur libre entre **180 px et 620 px** ;
- la largeur est persistée dans `localStorage`
  (`carte_left_width` / `carte_right_width`) et restaurée au chargement ;
- `MAP.resize()` est appelé au relâchement pour recadrer la carte ;
- poignée inactive quand le panneau est replié (`collapsed`) ;
- pendant le drag : curseur `col-resize` global et sélection de texte bloquée.

---

## 7. Détail des modifications par fichier

| Fichier | Modification |
|---|---|
| `templates/carte/index.html` | Suppression de la barre `.pg-tabs` (4 boutons). Ajout des en-têtes `.pg-panel-head` (← retour + titre + nom de couche) dans les 3 sous-panneaux. Champ « Couche » des formulaires masqué (`#qr-couche-field`, `#rm-couche-field`). Boutons « Filtrer » renommés + boutons « Réinitialiser le filtre » (`#btn-qr-reset`, `#btn-rm-reset`). Panneau Requête : barre ET/OU (`#qr-logique-field`), conteneur `#qr-extra-conditions`, bouton `#btn-qr-add-cond`. CSS : `.pg-panel-head`, `.pg-back-btn`, `.pg-panel-title`, `.pg-panel-couche`, `.panel-resize-handle`, `#qr-extra-conditions`. Script `initPanelResize`. |
| `carte/static/carte/js/map.js` | Deux nouveaux boutons par ligne couche : `.couche-multi-btn` (fa-sliders-h) et `.couche-select-btn` (fa-mouse-pointer). |
| `carte/static/carte/js/query.js` | Helpers globaux `applyLayerFilter` / `clearLayerFilter` / `FILTERED_LAYERS`. « Appliquer » → filtre carte au lieu de sélection. Gestion du bouton Réinitialiser. Handler `.couche-filter-btn` re-câblé vers `showPgPanel('requete')` + label d'en-tête. Conditions multiples ET/OU : blocs dynamiques (`_addExtraCondition`, `_collectAllConditions`), prévisualisation branchée sur l'API multicritère dès 2 conditions, invalidation du résultat à toute modification de critère. `requeteMulticritere()` renvoie désormais `{pks, count}` et lève une erreur (harmonisé avec `requeteSimple`). |
| `carte/static/carte/js/multiquery.js` | « Exécuter » → filtre carte. Bouton Réinitialiser. Nouveau handler `.couche-multi-btn` → `showPgPanel('multi')` + pré-sélection couche. |
| `carte/static/carte/js/selection.js` | `_initPgTabs()` remplacé par `window.showPgPanel()` + binding des `.pg-back-btn`. Nouveau `window.SELECTION_SCOPE` + `_scopedLayerIds()` appliqué au clic, au rectangle et à l'inversion. Handler `.couche-select-btn`. |

Aucune modification côté Django (API `requete/simple`, `requete/multicritere`,
`valeurs`, `extent` inchangées).

---

## 8. Procédure de test

1. Recharger la carte avec **Ctrl+F5** (vider le cache navigateur).
2. Vérifier que la barre d'onglets a disparu : seul le gestionnaire de couches
   s'affiche sous l'en-tête « Couches ».
3. Survoler une ligne (ex. *Bassins versants*) → 6 boutons apparaissent.
4. **Entonnoir** → le sous-panneau « Requête — Bassins versants » s'ouvre, la
   couche se coche, les champs se chargent. Choisir champ/opérateur/valeur →
   *Prévisualiser* (compte) → *Filtrer* : la carte ne montre plus que les
   entités correspondantes. *Réinitialiser le filtre* les réaffiche toutes.
   **« + Ajouter une condition »** → un 2ᵉ bloc apparaît avec un séparateur
   ET ; la barre « Combiner les conditions » permet de basculer en OU (les
   séparateurs suivent). *Prévisualiser* affiche « N résultats (2 conditions,
   OU) » et *Filtrer* applique le résultat combiné.
5. **Curseurs** → sous-panneau « Multicritère » avec une première condition
   pré-créée. Ajouter une 2ᵉ condition, basculer ET/OU, *Filtrer*.
6. **Pointeur** → sous-panneau « Sélection — <couche> ». Cliquer sur la carte :
   seules les entités de cette couche sont sélectionnables. ← retour → la
   sélection redevient globale.
7. **Palette / Centrer / Isoler** → comportement identique à avant (régression
   à vérifier).
8. Tirer la poignée entre panneau et carte → largeur ajustée, persistée après
   rechargement.

---

## 9. Limites et points d'attention

- **Filtre vs masque contextuel** : le masque du menu contextuel
  (`contextmenu.js`, double-clic / drill-down) utilise aussi `setFilter` sur la
  même couche. Le dernier appliqué gagne ; « Réinitialiser » de l'un efface le
  filtre de l'autre. Acceptable en l'état, à unifier si besoin (registre commun).
- Le filtre n'est **pas persisté** au rechargement de la page (volontaire).
- Décocher/recocher une couche conserve son filtre (la source MapLibre est
  gardée en mémoire) — le bandeau du sous-panneau permet de le retrouver.
- Le scope de sélection est levé uniquement par le bouton ← retour ; si
  l'utilisateur replie le panneau gauche pendant qu'un scope est actif, le
  scope reste posé.
- La largeur des lignes de couches : 6 boutons au survol — sur un panneau
  étroit (< 220 px), les libellés longs sont tronqués (ellipsis). Le
  redimensionnement du panneau compense.
