# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Django 6 + GeoDjango (PostGIS) web application for managing water resources in irrigated perimeters of southeastern Morocco (Tafilalet / Midelt). The platform combines hydrological analysis, structural diagnostics of hydraulic works, and water-balance computations (needs vs. resources) on a monthly hydrological calendar (September → August).

The Django project itself lives in [plateformeSIG/](plateformeSIG/) (the inner directory). The outer directory is a Python venv (`Include/`, `Lib/`, `Scripts/`, `pyvenv.cfg`), so all `manage.py` commands run from the inner project root.

## Commands

All commands are run from the inner Django project (`plateformeSIG/plateformeSIG/`):

```powershell
# Activate the venv (outer directory)
..\Scripts\Activate.ps1

# Or call the venv python directly without activation (more reliable in scripts / CI)
..\Scripts\python.exe manage.py runserver
..\Scripts\python.exe manage.py migrate

# Migrations
python manage.py makemigrations
python manage.py migrate

# Dev server (default http://127.0.0.1:8000)
python manage.py runserver

# Django shell with GIS
python manage.py shell

# Run all tests / a single app / a single test
python manage.py test
python manage.py test analyse_hydrologique
python manage.py test diagnostic.tests.SomeTestCase.test_method

# Create a superuser for /admin
python manage.py createsuperuser
```

There is no `requirements.txt`, lint config, or CI in the repo — dependencies live in the venv (Django, `django.contrib.gis`, `django.contrib.postgres`, numpy/matplotlib for charts, openpyxl for Excel export).

## Native dependencies (Windows)

GeoDjango requires native GDAL/GEOS/PROJ binaries from OSGeo4W. [plateformeSIG/settings.py](plateformeSIG/settings.py) hard-codes:

- `GDAL_LIBRARY_PATH = C:\OSGeo4W\bin\gdal312.dll`
- `GEOS_LIBRARY_PATH = C:\OSGeo4W\bin\geos_c.dll`
- `PROJ_LIB` / `PROJ_DATA` forced to `C:\OSGeo4W\share\proj` **before any GIS import** — this is intentional to override PostgreSQL's older bundled PROJ.

If you touch [settings.py](plateformeSIG/settings.py), preserve the PROJ env-var block at the top.

Database is PostgreSQL with **PostGIS** (engine `django.contrib.gis.db.backends.postgis`). Connection settings are read from environment variables / a local `.env` file (see [.env.example](.env.example)); dev defaults are user `postgres`, db `plateformeSIG`.

## Architecture

### Apps and their roles

Five Django apps in [plateformeSIG/plateformeSIG/](plateformeSIG/) (URL prefixes in [plateformeSIG/urls.py](plateformeSIG/urls.py)):

| App | URL prefix | Purpose |
|---|---|---|
| [compte/](compte/) | `/compte/` | Custom `Utilisateur` (AbstractUser) with `role` ∈ {visiteur, opérateur, éditeur}. Set as `AUTH_USER_MODEL`. |
| [analyse_hydrologique/](analyse_hydrologique/) | `/hydrologie/` | Bassins versants, stations pluvio/hydrométriques, Montana coefficients, flood-discharge analyses. |
| [diagnostic/](diagnostic/) | `/diagnostic/` | Périmètres agricoles + 7 ouvrage types (seuils, murs, séguias, barrages, khettaras, forages, prises locales) with structured state diagnostics. |
| [Besions_Ressources/](Besions_Ressources/) | `/bilan/` | Climate stations, crop Kc/Kr referential, monthly water-balance computations per périmètre. (Note: misspelled — should be "Besoins"; left as-is.) |
| [carte/](carte/) | — | `Province` / `Commune` reference geographies (no urls; used as FK targets). |

### Cross-app data flow

The three "domain" apps are intentionally coupled by foreign key:

- `diagnostic.Perimetre` is the central entity. All ouvrages (Seuil, MurProtection, Seguias, BarrageRetenue, Khettara, ForagePuits, PriseLocale) FK to it.
- Most ouvrages also FK to `analyse_hydrologique.BassinVersant` (used to derive Tc and crue parameters).
- `Besions_Ressources.BilanBesoinRessources` FKs into both worlds — `diagnostic.Perimetre` plus `StationClimatique`, optional `StationHydrometrique`, and a `BilanOuvrageAssocie` join table that polymorphically points at any of the 5 ouvrage types via 5 nullable FKs (exactly one is non-null per row, gated by `type_ouvrage`).
- `Besions_Ressources.Kc_Kr_culture` reuses the `CULTURES_TAFILALET` choices list defined in [diagnostic/models.py](diagnostic/models.py) — that constant is the single source of truth for crop names; import it rather than redefining.

When deleting/refactoring an ouvrage type, remember it has **three** consumers: its own diagnostic state model (`Etat<X>`), the `SguiaAssocie_OuvrageTete` N–N join, and `BilanOuvrageAssocie`.

### Diagnostic state pattern

Every ouvrage has a paired `Etat<X>` model with a `OneToOneField(primary_key=True)`. The Etat models hold structured ratings (0–5 from `NOTE_CHOICES` / `NOTE_SEGUIA_CHOICES`) and an `etat_general` from `ETAT_CONSTRUCTION_DIAG_CHOICES`. The legacy free-text `etat_*` fields on the ouvrage models are kept for backwards compatibility — new code should write to `Etat<X>` and treat the text fields as read-only legacy.

Most ouvrages also inherit `DiagnosticSuiviMixin` (date_diagnostic, defaut_ouvrage, saisi_par, valide_par).

### Schema evolution

The `diagnostic` app has 20+ migrations including a merge migration ([0018_merge_20260512_1058.py](diagnostic/migrations/0018_merge_20260512_1058.py)) — the schema actively evolves. When adding a field to an ouvrage:

1. Add the field on the ouvrage model if it's structural (geometry, dimensions, identity).
2. If it's a diagnostic rating, add it to the paired `Etat<X>` model instead (use `NOTE_CHOICES` or `NOTE_SEGUIA_CHOICES`).
3. Run `makemigrations diagnostic` and review the generated file before committing.
4. Never edit a past migration — always add a new one, even for cosmetic changes.

The `Besions_Ressources` app follows the same pattern (5+ migrations, including `Kc_Kr_culture` refactors).

### Hydrological calculation engine

The numeric core lives **outside** Django apps, in three sibling modules in [plateformeSIG/static/](plateformeSIG/static/):

- [hydrologie_bv.py](plateformeSIG/static/hydrologie_bv.py) → `HydroBV`, `HydroSP`, `HydroSH` classes for crue / flood-discharge analysis, consumed by [analyse_hydrologique/calculs.py](analyse_hydrologique/calculs.py).
- [Besions_Ressources.py](plateformeSIG/static/Besions_Ressources.py) → monthly water-balance classes (needs vs. resources), consumed by [Besions_Ressources/calculs.py](Besions_Ressources/calculs.py).
- [bilan1.py](plateformeSIG/static/bilan1.py) → earlier balance prototype, kept for reference.

Each `calculs.py` adapter injects `STATICFILES_DIRS[0]` into `sys.path` before importing, and provides `*_to_hydro()` / equivalent helpers converting Django ORM instances into the plain calculation objects. **If you move any of these modules, every adapter must be updated in lock-step.**

This means: editing the math formulas means editing the `static/*.py` modules, not the Django models.

Available formulas (`FORMULES_Q_DISPONIBLES` / `FORMULES_TC_DISPONIBLES`) and return periods (`PERIODES = [10, 20, 50, 100]`) are declared in [analyse_hydrologique/calculs.py](analyse_hydrologique/calculs.py) — keep them as the single source of truth.

### Hydrological calendar

All monthly arrays are **12 values in September → August order** (`MOIS_SEP_AOU` in [Besions_Ressources/calculs.py](Besions_Ressources/calculs.py)). This applies to: station temperatures, insolation, precipitations, Kc/Kr, observed monthly discharges (`debits_mensuels_annee_humide/normale/seche`), apports mensuels of barrages, etc. **Do not reorder to Jan→Dec** — the calculation engine assumes Sep→Août.

### SHP / GIS import

Multiple views accept ZIP-packaged shapefiles (`upload_shp`, `importer_bv_multiple`, and `*_shp_import` per ouvrage type). Field-name normalization tables like `SHP_FIELD_MAP` in [analyse_hydrologique/views.py](analyse_hydrologique/views.py) map common attribute aliases (ArcGIS naming variations, French/English, m² vs km²) to model fields. Add new aliases to these maps rather than enforcing strict naming on the input.

Geometries are stored in SRID 4326 in the DB, but raw coordinates in models are documented as "Nord Maroc, m" (EPSG:26191 — `SRID_NORD_MAROC = 26191`).

### Templates & static

- Templates: [templates/](templates/) at the project root (registered via `TEMPLATES.DIRS`) — organized by app subdirectory. App-level `templates/` dirs also work (`APP_DIRS=True`).
- Static: two sources — [plateformeSIG/static/](plateformeSIG/static/) (project static, includes the calculation modules and shapefile fixtures) and standard app `static/` dirs. `STATIC_ROOT` is `BASE_DIR/static` (collectstatic target).

### Navigation and role gating

[templates/base.html](templates/base.html) is the navigation entry point and acts as the feature map of the platform. Menu visibility is gated by template-level `{% if user.role == '...' %}` checks:

- **visiteur** → Accueil, À propos only.
- **opérateur** → adds Analyse (hydrologique, bilan, hydraulique des canaux), Dimensionnement, Plan d'action dropdowns.
- **opérateur + éditeur** → adds Diagnostic dropdown (création de périmètre / ouvrages, suivi et évaluation).

**Important security note**: role gating is template-only (UI). View-side decorators are limited to `@login_required` — there is no `@role_required('operateur')` in place. A direct URL (`/diagnostic/...`) is not refused to a logged-in visiteur. This is a known gap; tighten it before any production deployment.

Links with `href="#"` in the menu (Carte, Hydraulique des canaux, Dimensionnement des seuils/canaux, Analyse économique, Plan d'action items, À propos) are **roadmap placeholders, not broken links**.

## Pending modules

The **efficiences** app is specified ([../ETAT_AVANCEMENT_EFFICIENCES.md](../ETAT_AVANCEMENT_EFFICIENCES.md)) but not yet built. When it lands, it will:

- Add `et0_mm_jour` field on `Perimetre` (Lot 0 schema change).
- Add efficience persistence fields on `Seguias` (`efficience_calculee`, `perte_infiltration_m3s`, `perte_vaporisation_m3s`, `date_dernier_calcul`).
- Introduce a new `Efficience` aggregation entity (per perimetre + ouvrage de tête, with cascade: tronçon → catégorie P/S/T → global).
- Replace the « Hydraulique des canaux » `href="#"` placeholder in [base.html](templates/base.html) with a real link to `/efficiences/`.

Until then, treat any feature request mentioning "efficience des réseaux" / "rendement de canaux" as out-of-scope for the current codebase.

## Language note

User-facing strings, model `verbose_name`s, choices, comments, and many identifiers are in **French**. Some app/field names are misspelled (`Besions_Ressources` → "Besoins", `efficiance` → "efficience", `type_deguia` → "type_seguia", `coordonnes_x` → "coordonnees_x"). These are baked into migrations and templates — do not "fix" them without a migration plan.
