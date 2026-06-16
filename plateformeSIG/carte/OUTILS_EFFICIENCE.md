# Box « Efficience réseau » — panneau droit Outils de la Carte

Documentation des outils de la box **Efficience réseau**. Ils réutilisent les
services de l'app `efficiences` et le champ persistant
`diagnostic.TronconSeguia.efficience_calculee`.

> **Mises à jour Lots A–G** :
> - **Efficience ouvrage de tête** et **Profil de pertes (séguia)** : fenêtre
>   **`FloatingChart`** multi-instances (point 3). Sélection encore par menu
>   déroulant (conversion sélection carte = ajout backend à prévoir).
> - **Rendement tronçons (carte)** : **modes** (point 4) — seuils fixes (continu,
>   défaut) ou classes (quantiles) sur la couche de lignes WebGL.

---

## 1. Efficience ouvrage de tête

- **But** : cascade Principale / Secondaire / Tertiaire → globale d'un ouvrage de tête.
- **Module** : fenêtre flottante `#ef-window` (barres colorées).
- **Sélection** : menu listant le **dernier `Efficience` par ouvrage** (lecture,
  pas de recalcul DB).
- **Données** : `GET api/efficiences/liste/` (cascade + nombre de tronçons P/S/T).

## 2. Profil de pertes (séguia)

- **But** : débit amont→aval + pertes (infiltration / vaporisation) par tronçon.
- **Module** : fenêtre flottante (barres **empilées** : débit aval + Pi + Pv =
  débit amont).
- **Sélection** : séguia (menu).
- **Données** : `GET api/seguia/<pk>/profil/` → propagation séquentielle du débit
  via `efficiences.services.efficience_troncon.calculer_efficience_troncon`
  (`persister=False` — lecture seule, aucune écriture).

## 3. Rendement tronçons (carte)

- **But** : tronçons de séguias colorés par `efficience_calculee` (%).
- **Module** : carte, **slot `resultat`** — couche de lignes ajoutée (rampe
  rouge < 50 → vert ≥ 90 ; gris = non calculé), retirée via `cleanup`.
- **Données** : `GET api/couche/troncons_seguias/?limit=2000` (champ
  `efficience_calculee` exposé) — aucune vue dédiée.

---

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| [carte/api_views.py](api_views.py) | `efficiences_liste`, `seguias_liste`, `seguia_profil`. |
| [carte/urls.py](urls.py) | Routes `api/efficiences/liste/`, `api/seguias/liste/`, `api/seguia/<pk>/profil/`. |
| [carte/static/carte/js/outils-efficience.js](static/carte/js/outils-efficience.js) | Contrôleur (fenêtre `#ef-window`). |
| `templates/carte/index.html` | Box, 3 sous-panneaux, fenêtre `#ef-window`. |

## Capture Layout / PDF

La couche « Rendement tronçons » (WebGL) est capturée nativement. Les fenêtres
(Efficience, Profil) sont hors carte.
