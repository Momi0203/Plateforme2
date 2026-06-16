# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Django 6 + GeoDjango (PostGIS) web application for managing water resources in irrigated perimeters of southeastern Morocco (Tafilalet / Midelt). The platform combines hydrological analysis, structural diagnostics of hydraulic works, and water-balance computations (needs vs. resources) on a monthly hydrological calendar (September → August).

The outer directory is a Python venv (`Include/`, `Lib/`, `Scripts/`, `pyvenv.cfg`). The Django project lives in the inner [plateformeSIG/](plateformeSIG/) directory. All `manage.py` commands run from there.

## Commands

All commands run from inside [plateformeSIG/](plateformeSIG/):

```powershell
# Activate the venv (run from outer directory)
..\Scripts\Activate.ps1

# Or call the venv python directly (works from the inner project dir)
..\Scripts\python.exe manage.py runserver
..\Scripts\python.exe manage.py migrate

# Migrations
python manage.py makemigrations
python manage.py migrate

# Dev server (default http://127.0.0.1:8000)
python manage.py runserver

# Django shell with GIS
python manage.py shell

# Run all tests / a single app / a single test class
python manage.py test
python manage.py test analyse_hydrologique
python manage.py test diagnostic.tests.SomeTestCase.test_method

# Create a superuser for /admin
python manage.py createsuperuser
```

There is no `requirements.txt`, lint config, or CI — dependencies live in the venv (Django, `django.contrib.gis`, `django.contrib.postgres`, numpy/matplotlib, openpyxl).

## Native dependencies (Windows)

GeoDjango requires native GDAL/GEOS/PROJ binaries from OSGeo4W. [plateformeSIG/settings.py](plateformeSIG/settings.py) hard-codes:

- `GDAL_LIBRARY_PATH = C:\OSGeo4W\bin\gdal312.dll`
- `GEOS_LIBRARY_PATH = C:\OSGeo4W\bin\geos_c.dll`
- `PROJ_LIB` / `PROJ_DATA` forced to `C:\OSGeo4W\share\proj` **before any GIS import** — this overrides PostgreSQL's older bundled PROJ intentionally.

If you touch [settings.py](plateformeSIG/settings.py), preserve the PROJ env-var block at the top.

Database is PostgreSQL with **PostGIS** (`django.contrib.gis.db.backends.postgis`). Connection settings are read from environment variables / a local `.env` file (see [.env.example](plateformeSIG/.env.example)); dev defaults are user `postgres`, db `plateformeSIG`.

## Architecture

### Apps and their roles

Six Django apps under [plateformeSIG/](plateformeSIG/) (URL prefixes in [plateformeSIG/urls.py](plateformeSIG/urls.py)):

| App | URL prefix | Purpose |
|---|---|---|
| [compte/](plateformeSIG/compte/) | `/compte/` | Custom `Utilisateur` (AbstractUser) with `role` ∈ {visiteur, opérateur, éditeur}. Set as `AUTH_USER_MODEL`. |
| [analyse_hydrologique/](plateformeSIG/analyse_hydrologique/) | `/hydrologie/` | Bassins versants, stations pluvio/hydrométriques, Montana coefficients, flood-discharge analyses. |
| [diagnostic/](plateformeSIG/diagnostic/) | `/diagnostic/` | Périmètres agricoles + 7 ouvrage types (seuils, murs, séguias, barrages, khettaras, forages, prises locales) with structured state diagnostics. |
| [Besions_Ressources/](plateformeSIG/Besions_Ressources/) | `/bilan/` | Climate stations, crop Kc/Kr referential, monthly water-balance computations per périmètre. (Misspelled — should be "Besoins"; do not rename.) |
| [efficiences/](plateformeSIG/efficiences/) | `/efficiences/` | `Efficience` aggregation model: network efficiency per périmètre + ouvrage de tête, cascade P/S/T → global. |
| [carte/](plateformeSIG/carte/) | — | `Province` / `Commune` reference geographies (no URLs; FK targets only). |

### Cross-app data flow

- `diagnostic.Perimetre` is the central entity. All ouvrages (Seuil, MurProtection, Seguias, BarrageRetenue, Khettara, ForagePuits, PriseLocale) FK to it.
- Most ouvrages also FK to `analyse_hydrologique.BassinVersant` (used to derive Tc and crue parameters).
- `Besions_Ressources.BilanBesoinRessources` FKs into both worlds — `diagnostic.Perimetre` plus `StationClimatique`, optional `StationHydrometrique`, and a `BilanOuvrageAssocie` join table that polymorphically points at any of the 5 ouvrage types via 5 nullable FKs (exactly one non-null per row, gated by `type_ouvrage`).
- `Besions_Ressources.Kc_Kr_culture` reuses `CULTURES_TAFILALET` from [diagnostic/models.py](plateformeSIG/diagnostic/models.py) — that constant is the single source of truth for crop names.
- `efficiences.Efficience` FKs to `diagnostic.Perimetre`; it identifies the ouvrage de tête via `ouvrage_tete_type` (choices: seuil / prise_locale / khettara / forage_puits / barrage_retenue) + `ouvrage_tete_id` (generic FK pattern, not a real FK).

When deleting/refactoring an ouvrage type, it has **three** consumers: its `Etat<X>` diagnostic state model, the `SguiaAssocie_OuvrageTete` N–N join, and `BilanOuvrageAssocie` — plus `Efficience.OUVRAGE_TYPE_CHOICES` if it is an ouvrage de tête type.

### Diagnostic state pattern

Every ouvrage has a paired `Etat<X>` model with `OneToOneField(primary_key=True)`. Etat models hold structured ratings (0–5 from `NOTE_CHOICES` / `NOTE_SEGUIA_CHOICES`) and an `etat_general` from `ETAT_CONSTRUCTION_DIAG_CHOICES`. Legacy free-text `etat_*` fields on ouvrage models are kept for backwards compatibility — new code writes to `Etat<X>`, treats text fields as read-only.

Most ouvrages inherit `DiagnosticSuiviMixin` (date_diagnostic, defaut_ouvrage, saisi_par, valide_par).

`statut` on all ouvrages and `Perimetre` now has choices `non_valide` / `valide` (renamed from `brouillon` in migration 0030; the field default is still `'brouillon'` at DB level — do not add new `brouillon` choices).

### Schema evolution

The `diagnostic` app has 31+ migrations including a merge ([0018_merge_20260512_1058.py](plateformeSIG/diagnostic/migrations/0018_merge_20260512_1058.py)). Migration 0031 (June 2026) added six volume/excédent-déficit fields to `Perimetre` (`volume_annee_humide/normale/seche`, `volume_excedent_deficit_humide/normale/seche`).

When adding a field to an ouvrage:
1. Add structural fields (geometry, dimensions, identity) to the ouvrage model.
2. Add diagnostic ratings to the paired `Etat<X>` model using `NOTE_CHOICES` or `NOTE_SEGUIA_CHOICES`.
3. Run `makemigrations diagnostic` and review the generated file.
4. Never edit a past migration — always add a new one.

The `Besions_Ressources` app follows the same pattern (5+ migrations).

### Hydrological calculation engine

The numeric core lives **outside** Django apps in three sibling modules in [plateformeSIG/static/](plateformeSIG/static/):

- [hydrologie_bv.py](plateformeSIG/static/hydrologie_bv.py) → `HydroBV`, `HydroSP`, `HydroSH` classes, consumed by [analyse_hydrologique/calculs.py](plateformeSIG/analyse_hydrologique/calculs.py).
- [Besions_Ressources.py](plateformeSIG/static/Besions_Ressources.py) → monthly water-balance classes, consumed by [Besions_Ressources/calculs.py](plateformeSIG/Besions_Ressources/calculs.py).
- [bilan1.py](plateformeSIG/static/bilan1.py) → earlier balance prototype, kept for reference.

Each `calculs.py` adapter injects `STATICFILES_DIRS[0]` into `sys.path` before importing and provides `*_to_hydro()` helpers converting ORM instances to plain calculation objects. **If you move any of these modules, every adapter must be updated in lock-step.**

`FORMULES_Q_DISPONIBLES`, `FORMULES_TC_DISPONIBLES`, and `PERIODES = [10, 20, 50, 100]` are declared in [analyse_hydrologique/calculs.py](plateformeSIG/analyse_hydrologique/calculs.py) — single source of truth.

### Hydrological calendar

All monthly arrays are **12 values in September → August order** (`MOIS_SEP_AOU`). This applies to: temperatures, insolation, precipitations, Kc/Kr, observed monthly discharges, barrage monthly inflows, etc. **Do not reorder to Jan→Dec** — the calculation engine assumes Sep→Août.

### SHP / GIS import

Multiple views accept ZIP-packaged shapefiles (`upload_shp`, `importer_bv_multiple`, `*_shp_import` per ouvrage). Field-name normalization tables like `SHP_FIELD_MAP` in [analyse_hydrologique/views.py](plateformeSIG/analyse_hydrologique/views.py) map common attribute aliases to model fields. Add new aliases to these maps rather than enforcing strict naming on the input.

Geometries are stored in SRID 4326; raw coordinates in models are Nord Maroc (EPSG:26191 — `SRID_NORD_MAROC = 26191`).

### Templates and static

- Templates: [templates/](plateformeSIG/templates/) at the project root, organized by app subdirectory. App-level `templates/` dirs also work (`APP_DIRS=True`).
- Static: [plateformeSIG/static/](plateformeSIG/static/) (project static, includes calculation modules + shapefile fixtures) and standard app `static/` dirs. `STATIC_ROOT` is `BASE_DIR/static` (collectstatic target).

### Navigation and role gating

[templates/base.html](plateformeSIG/templates/base.html) is the navigation entry point. Menu visibility is gated by `{% if user.role == '...' %}` template checks:

- **visiteur** → Accueil, À propos only.
- **opérateur** → adds Analyse (hydrologique, bilan, hydraulique des canaux), Dimensionnement, Plan d'action.
- **opérateur + éditeur** → adds Diagnostic (création périmètre/ouvrages, suivi et évaluation).

**Security note**: role gating is template-only. Views only have `@login_required` — no `@role_required('operateur')`. A direct URL is not blocked to a logged-in visiteur. Tighten before production.

Links with `href="#"` in the menu (Carte, Hydraulique des canaux, Dimensionnement, Analyse économique, Plan d'action, À propos) are roadmap placeholders, not broken links.

## Language note

User-facing strings, `verbose_name`s, choices, comments, and many identifiers are in **French**. Some names are misspelled (`Besions_Ressources` → "Besoins", `efficiance` → "efficience", `type_deguia` → "type_seguia", `coordonnes_x` → "coordonnees_x"). These are baked into migrations and templates — do not "fix" them without a migration plan.
