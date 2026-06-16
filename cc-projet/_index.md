# CDC Module Carte — Index de navigation

> **Plateforme SIG — Gestion des ressources en eau irriguées — Tafilalet / Midelt**
> Version 2.0 — Juin 2026

## Comment utiliser ces fichiers avec Claude Code

```
# Exemple : coder le panneau gauche
"Lis cc-projet/03_panneau_gauche.md et implémente la section 5.1.1 Couches"

# Exemple : coder une API
"Lis cc-projet/06_api_architecture.md section 7.1 et génère les vues Django"

# Exemple : tout le contexte
"Lis cc-projet/_index.md pour le contexte, puis cc-projet/05_outils_metier.md pour la Box Séguia"
```

---

## Fichiers disponibles

| Fichier | Sections CDC | Contenu |
|---|---|---|
| [00_resume_executif.md](00_resume_executif.md) | Synthèse | Vue d'ensemble, stack, contraintes clés |
| [01_contexte_objectifs.md](01_contexte_objectifs.md) | §1 + §2 | Contexte, base de données, objectifs |
| [02_perimetre_couches.md](02_perimetre_couches.md) | §3 + §4 | Fonctionnalités MUST/SHOULD, 15 couches géo |
| [03_panneau_gauche.md](03_panneau_gauche.md) | §5.1 | Couches, sélection, requêtes, symbologie, double-clic |
| [04_vues_centrales.md](04_vues_centrales.md) | §5.2 + §6 | Carte, dashboard, tableau attributaire, synchronisation |
| [05_outils_metier.md](05_outils_metier.md) | §5.3 | 7 boîtes outils métier + outils génériques |
| [06_api_architecture.md](06_api_architecture.md) | §7 + §9 + §10 | Endpoints API, architecture, LAYER_REGISTRY |
| [07_securite_contraintes.md](07_securite_contraintes.md) | §8 + §11 | Rôles, sécurité, contraintes, évolutivité |
| [08_livrables_recette.md](08_livrables_recette.md) | §12 + §13 | Critères d'acceptation, livrables, planning |

---

## Règle d'évolutivité (à lire absolument)

> **Toute valeur d'un champ à choix fermé (nature, état, type...) doit être lue
> dynamiquement depuis l'API — jamais codée en dur dans le JavaScript.**
> Endpoint : `GET /carte/api/couche/<nom>/champs/<champ>/valeurs/`

## Stack technique

- Django 6 + GeoDjango (PostGIS) — Python 3.14
- PostgreSQL 15 + PostGIS — SRID 4326
- GDAL 3.12 / GEOS / PROJ via OSGeo4W
- MapLibre GL JS (rendu carte) — Chart.js (graphiques)
- Calendrier hydrologique : **Sep → Août** (jamais Jan → Déc)

## Apps Django existantes (ne pas modifier leurs modèles)

| App | Rôle |
|---|---|
| `compte` | Utilisateur + rôles : visiteur / opérateur / éditeur |
| `analyse_hydrologique` | BassinVersant, Stations, ReseauHydrographique |
| `diagnostic` | Perimetre + 7 types d'ouvrages + Etat<X> |
| `Besions_Ressources` | StationClimatique, BilanBesoinRessources |
| `carte` | Province, Commune — **app à développer** |
