# Outil « Comparaison besoin » — Box « Outils périmètre » (panneau droit de la Carte)

Documentation fonctionnelle et technique de l'outil **Comparaison besoin**,
accessible depuis le panneau droit **Outils** de la carte SIG (`/carte/`), dans
la box **Outils périmètre** (à côté de l'outil **Besoin**).

> Outil frère de l'outil **Besoin** (voir [OUTIL_BESOIN.md](OUTIL_BESOIN.md)).
> Même mode de sélection et même source de données. Le résultat n'est pas un
> rendu thématique sur la carte (cercles/camemberts) mais un **graphe** affiché
> dans une **fenêtre flottante déplaçable**, posée par-dessus la carte — dans le
> même template `index` (pas de nouvelle page ni d'onglet).

---

## 1. Objectif

Comparer, pour une **année de référence** (humide / normale / sèche) et un
ensemble de périmètres sélectionnés (**25 au maximum**), trois grandeurs côte à
côte sous forme de **graphe en barres groupées** :

- le **volume de besoin** (`volume_annee_*`) — bleu ;
- la part **excédentaire** (solde positif) — vert, au-dessus de 0 ;
- la part **déficitaire** (solde négatif) — rouge, **toujours négative** (sous 0).

Les valeurs sont **lues telles quelles** en base — aucun calcul.

---

## 2. Emplacement et résultat

```
Panneau droit « Outils »
└── Box « Outils périmètre »  (accordéon)
    ├── Outil « Besoin »              → rendu thématique sur la carte
    └── Outil « Comparaison besoin »  → sous-panneau → fenêtre flottante (sur la carte)
```

Le clic sur **Comparaison besoin** masque la liste des outils et affiche un
sous-panneau (mêmes champs et style que l'outil Besoin). Le bouton **Générer le
graphique** ouvre une **fenêtre flottante** (`#cb-window`) au-dessus de la
carte : on la **déplace librement** en glissant sa barre de titre (comme une
boîte de dialogue), on la redimensionne par le coin, et on la ferme par la croix.

---

## 3. Champs du sous-panneau

| Champ | Type | Comportement |
|---|---|---|
| **Périmètres sélectionnés** | Lecture seule | Rempli depuis la sélection carte (`window.selection_par_couche.perimetres`). « 0 — toute la couche » si rien n'est sélectionné. |
| **Avertissement 25** | Bandeau | Visible si > 25 périmètres sélectionnés ; seuls les 25 premiers seront comparés. |
| **Année** | Liste | `Année normale` (défaut) · `Année humide` · `Année sèche`. |
| **Générer le graphique** | Bouton | Récupère les données et dessine le graphe dans la fenêtre flottante. |

- **Avec sélection** → comparaison des périmètres sélectionnés (tronqués à 25).
- **Sans sélection** → toute la couche, **plafonnée aux 25 premiers** périmètres
  ayant une valeur de besoin pour l'année (bandeau de troncature si dépassement).

---

## 4. Source des données et conventions de signe

- Modèle : `diagnostic.Perimetre`.
- Champs (migration 0031) :
  - besoin : `volume_annee_humide / normale / seche` ;
  - solde  : `volume_excedent_deficit_humide / normale / seche` (signé).
- Un périmètre n'apparaît que s'il a une **valeur de besoin non nulle** pour
  l'année demandée.

Le solde signé est scindé côté serveur :

| Grandeur | Calcul | Signe |
|---|---|---|
| `excedent` | `solde` si `solde > 0` sinon `0` | ≥ 0 |
| `deficit`  | `solde` si `solde < 0` sinon `0` | **≤ 0 (toujours négatif)** |
| `solde`    | valeur brute | signé |

Le **déficit reste négatif** : il s'affiche donc sous l'axe zéro du graphe,
visuellement opposé à l'excédent.

---

## 5. Fenêtre flottante (résultat)

Élément `#cb-window` dans `templates/carte/index.html` :

- **Barre de titre** (poignée de déplacement) : titre + année + bouton fermer.
- **Statut** : message de chargement / succès / erreur (+ note de troncature).
- **Graphe** : `Chart.js` v4 (déjà chargé par `index.html`), barres groupées
  Besoin (bleu) · Excédent (vert) · Déficit (rouge). Largeur ∝ nombre de
  périmètres (scroll horizontal interne au besoin).
- **Comportement** : déplaçable (drag sur l'en-tête), redimensionnable
  (`resize: both`), reste partiellement visible à l'écran.

L'instance Chart.js est détruite/recréée à chaque exécution et à la fermeture.

---

## 6. API / Endpoint

```
GET /carte/api/perimetres/comparaison-besoin/?annee=<humide|normale|seche>&pks=<id,id,…>
```

| Paramètre | Obligatoire | Description |
|---|---|---|
| `annee` | non (défaut `normale`) | Année de référence. |
| `pks` | non | Périmètres sélectionnés (sinon toute la couche, plafonné à 25). |

### Réponse (JSON)

```json
{
  "annee": "normale",
  "count": 1,
  "total": 1,
  "tronque": false,
  "perimetres": [
    { "pk": 8, "nom": "AHOULI", "besoin": 121195.0,
      "excedent": 85505.0, "deficit": 0.0, "solde": 85505.0 }
  ]
}
```

Authentification : `@api_login_required` (`@require_GET`).

---

## 7. Fichiers concernés

| Fichier | Rôle |
|---|---|
| [carte/api_views.py](api_views.py) | Vue `perimetres_comparaison_besoin` (JSON, plafond 25, scission excédent/déficit, déficit négatif). |
| [carte/urls.py](urls.py) | Route `api/perimetres/comparaison-besoin/`. |
| [carte/static/carte/js/outils-perimetre.js](static/carte/js/outils-perimetre.js) | Sous-panneau, compteur, fetch, graphe Chart.js, fenêtre déplaçable. |
| `templates/carte/index.html` | Item d'outil, sous-panneau, fenêtre flottante `#cb-window`, CSS. |

---

## 8. Workflow utilisateur

1. (Optionnel) Sélectionner ≤ 25 périmètres sur la carte.
2. Panneau droit **Outils** → **Outils périmètre** → **Comparaison besoin**.
3. Choisir l'**année**.
4. **Générer le graphique** → la fenêtre flottante s'affiche sur la carte.
5. Déplacer / redimensionner la fenêtre, puis la fermer par la croix.

---

## 9. Limites connues / évolutions possibles

- Plafond fixe de **25 périmètres** (`_COMPARAISON_MAX` côté serveur,
  `COMP_MAX` côté JS) — au-delà, troncature + bandeau d'alerte.
- Aucune logique de **calcul** : suppose les `volume_*` déjà renseignés en base.
- Pistes : export CSV/PNG du graphe, tri (par besoin / solde), bascule barres
  empilées, mémorisation de la position de la fenêtre.
