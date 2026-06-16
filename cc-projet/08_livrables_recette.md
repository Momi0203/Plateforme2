---
section: "08"
titre: "Critères d'acceptation et livrables"
version: "2.0"
date: "2026-06-04"
tags: [recette, tests, livrables, planning]
---

# §12 — Critères d'acceptation et §13 — Livrables

---

## 12. Critères d'acceptation (tests de recette)

| ID | Scénario | Résultat attendu |
|---|---|---|
| CA-01 | Ouvrir `/carte/` avec compte visiteur | Carte en lecture seule. Aucun bouton Requête/Outils/Export visible. |
| CA-02 | Ouvrir `/carte/` avec compte opérateur | Tous les panneaux accessibles. Tableau sans bouton Éditer. |
| CA-03 | Activer/désactiver la couche Périmètres | Couche disparaît/réapparaît sans rechargement de page. |
| CA-04 | Sélectionner 3 seuils par rectangle | 3 entités surlignées sur carte + 3 lignes surlignées tableau + dashboard recalculé sur ces 3. |
| CA-05 | Requête simple : Seuils `statut = 'valide'` | Seuls les seuils validés sélectionnés. Compteur correct. |
| CA-06 | Double-clic sur un seuil | Zoom sur le BV associé + affichage réseau hydro classifié par grid_code. |
| CA-07 | Double-clic sur une province | Zoom + affichage communes de cette province uniquement. |
| CA-08 | Tampon 500 m sur périmètre sélectionné | Nouvelle couche temporaire dans le gestionnaire avec géométrie correcte. |
| CA-09 | Export tableau seuils en Excel | Fichier .xlsx téléchargé avec colonnes et données correctes. |
| CA-10 | Export carte PDF A3 Paysage 300 dpi | PDF avec étendue visible, légende, flèche nord, échelle. |
| CA-11 | Clic segment donut "Mauvais" (dashboard seuils) | Seuils mauvais sélectionnés sur la carte et dans le tableau. |
| CA-12 | Ajouter la valeur `PVC` dans `NATURE_SEGUIA_CHOICES` | Légende symbologie et filtres tableau affichent `PVC` automatiquement sans toucher au JS. |
| CA-13 | Appel `/carte/api/couche/seuils/` sans connexion | HTTP 403. |
| CA-14 | Requête multicritère : Seuils état général = 'mauvais' OU 't_mauvais' | Seuls ces seuils sélectionnés. |
| CA-15 | Calculer efficience tronçons séguia sélectionnés | Valeurs `efficience_calculee`, `perte_infiltration_m3s`, `perte_vaporisation_m3s` mises à jour. |

---

## 13. Livrables attendus

| # | Livrable | Format |
|---|---|---|
| L-01 | Code source app `carte/` complète | Python / HTML / JS / CSS |
| L-02 | Migrations Django (StyleCouche + RequeteNommee) | Fichiers Python |
| L-03 | LAYER_REGISTRY complet (`carte/layers.py`) | Python |
| L-04 | Tests unitaires et d'intégration (couverture ≥ 70%) | `carte/tests.py` |
| L-05 | Mise à jour `CLAUDE.md` section carte/ | Markdown |
| L-06 | Guide utilisateur par rôle | PDF ou HTML |
| L-07 | Rapport de recette avec captures d'écran | Word / PDF |

---

## Planning indicatif (10 semaines)

| Phase | Contenu | Durée |
|---|---|---|
| Phase 0 — Prototypage | MapLibre GL JS, 1 couche GeoJSON, API `/carte/api/couches/`, maquette UI | 1 semaine |
| Phase 1 — Couches et visualisation | LAYER_REGISTRY complet, gestionnaire de couches, symbologie simple + catégorisée, fonds Esri | 2 semaines |
| Phase 2 — Sélection et requêtes | Outils de sélection, requête simple, requête multicritère (+ RM-07), synchronisation carte↔tableau | 2 semaines |
| Phase 3 — Tableau et dashboard | Tableau attributaire complet, 4 widgets préconfigurés, synchronisation dashboard, double-clic drill-down | 2 semaines |
| Phase 4 — Outils et exports | Boîtes outils génériques + 7 boîtes métier (scoring, efficience, Manning), export carte PDF, CSV/Excel | 2 semaines |
| Phase 5 — Finitions et recette | Sécurité (décorateurs rôles), tests, documentation, recette 15 critères | 1 semaine |

---

## Ordre recommandé pour commencer à coder

```
1. Créer l'app carte/ + urls.py + vue HTML vide
2. Écrire LAYER_REGISTRY (layers.py) pour les 15 couches
3. Écrire api_views.py : endpoint /couches/ et /couche/<nom>/
4. Intégrer MapLibre GL JS + afficher une couche (seuils)
5. Gestionnaire de couches (panneau gauche)
6. Sélection + tableau attributaire basique
7. Requête simple
8. Dashboard (Chart.js)
9. Outils génériques (tampon)
10. Boîtes métier (scoring Seuil en premier)
```
