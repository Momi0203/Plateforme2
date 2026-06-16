# Box « Bilan eau » — panneau droit Outils de la Carte

Documentation des outils de la box **Bilan eau**. Ils réutilisent les données et
fonctions de l'app `Besions_Ressources` et passent par **`CarteRendu`**.

> **Mises à jour Lots A–G** :
> - **Bilan mensuel** : menu déroulant supprimé → **sélection carte** d'un
>   périmètre (point 1) ; fenêtre **`FloatingChart`** multi-instances (point 3).
> - **ET0 climatique** : **sélection carte** + **multi-stations** (1 courbe par
>   station, plafond 12 — point 2) ; `FloatingChart`.
> - **Taux de couverture** : **modes** de présentation (point 4) — classes fixes
>   (défaut), aplat (couche `lyr-perimetres`), cercles classés, cercles
>   proportionnels — via `RenduCarte.renderThematique`.

> **Principe** : lecture des résultats déjà calculés (dernier
> `BilanBesoinRessources` du périmètre). Le calcul complet reste dans l'app Bilan.

---

## 1. Bilan mensuel

- **But** : besoins vs ressources (12 mois Sep→Aoû) + solde (excédent/déficit).
- **Module** : fenêtre flottante `#bl-window` (barres groupées Besoins / Ressources).
- **Sélection** : périmètre (menu) + année (normale / humide / sèche).
- **Données** : `GET api/perimetre/<pk>/bilan-mensuel/?annee=` — lecture du dernier
  `resultats_bilan_<annee>` (clés `besoins_m3`, `ressources_m3`, `deficit_m3`,
  `excedent_m3`, totaux).

## 2. Taux de couverture (carte)

- **But** : % de couverture = `total_ressources / total_besoins × 100` par périmètre.
- **Module** : carte, **slot `resultat`** — cercles **classés** :
  vert ≥ 100 % · jaune 80–100 · orange 50–80 · rouge < 50.
- **Données** : `GET api/perimetres/couverture/?annee=&pks=` — point_on_surface +
  totaux du dernier bilan.

## 3. ET0 climatique

- **But** : courbe d'évapotranspiration de référence mensuelle.
- **Module** : fenêtre flottante (Chart.js ligne).
- **Sélection** : station climatique (menu).
- **Données** : `GET api/station-clim/<pk>/eto/` →
  `Besions_Ressources.calculs.calculer_eto(temperatures, taux_insolation, latitude)`.

---

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| [carte/api_views.py](api_views.py) | `perimetre_bilan_mensuel`, `perimetres_couverture`, `station_clim_eto`. |
| [carte/urls.py](urls.py) | Routes `api/perimetre/<pk>/bilan-mensuel/`, `api/perimetres/couverture/`, `api/station-clim/<pk>/eto/`. |
| [carte/static/carte/js/outils-bilan.js](static/carte/js/outils-bilan.js) | Contrôleur (fenêtre `#bl-window`). |
| `templates/carte/index.html` | Box, 3 sous-panneaux, fenêtre `#bl-window`. |

## Capture Layout / PDF

Les cercles « Taux de couverture » sont recomposés via `CarteRendu.getOverlay()`
(type `circle`). Les fenêtres (Bilan mensuel, ET0) sont hors carte.
