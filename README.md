# Plateforme2 — Plateforme SIG de gestion des ressources en eau

Application web **Django 6 + GeoDjango (PostGIS)** pour la gestion des ressources en
eau dans les périmètres irrigués du sud-est marocain (Tafilalet / Midelt). Elle combine
l'analyse hydrologique, le diagnostic structurel des ouvrages hydrauliques et le calcul
du bilan hydrique (besoins vs. ressources) sur un calendrier hydrologique mensuel
(septembre → août).

## Modules (apps Django)

| App | Préfixe URL | Rôle |
|---|---|---|
| `compte` | `/compte/` | Utilisateur personnalisé avec rôles (visiteur / opérateur / éditeur) |
| `analyse_hydrologique` | `/hydrologie/` | Bassins versants, stations, coefficients de Montana, débits de crue |
| `diagnostic` | `/diagnostic/` | Périmètres agricoles + 7 types d'ouvrages et leurs états |
| `Besions_Ressources` | `/bilan/` | Stations climatiques, référentiel Kc/Kr, bilan hydrique mensuel |
| `efficiences` | `/efficiences/` | Efficience des réseaux par périmètre et ouvrage de tête |
| `plan_action` | `/plan-action/` | Plans d'action, calendrier, suivi |
| `doleances` | `/doleances/` | Doléances et demandes |
| `carte` | — | Géographies de référence (Province / Commune) |

## Prérequis

- Python 3.13 (un venv est utilisé en développement)
- PostgreSQL **avec l'extension PostGIS**
- Binaires natifs **GDAL / GEOS / PROJ** (sous Windows : OSGeo4W).
  Les chemins sont configurés dans `plateformeSIG/plateformeSIG/settings.py`
  (`GDAL_LIBRARY_PATH`, `GEOS_LIBRARY_PATH`, `PROJ_LIB` / `PROJ_DATA`).

## Installation

```bash
# 1. Cloner
git clone https://github.com/Momi0203/Plateforme2.git
cd Plateforme2

# 2. Créer et activer un environnement virtuel
python -m venv venv
# Windows : venv\Scripts\activate    |    Linux/macOS : source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
#    Copier l'exemple puis renseigner vos valeurs (mot de passe DB, SECRET_KEY…)
cd plateformeSIG
cp .env.example .env        # Windows : copy .env.example .env

# 5. Créer la base PostgreSQL + activer PostGIS, puis migrer
python manage.py migrate

# 6. Créer un superutilisateur
python manage.py createsuperuser

# 7. Lancer le serveur de développement
python manage.py runserver
```

## Configuration (`.env`)

Les secrets ne sont **pas** versionnés. La configuration est lue depuis un fichier
`.env` placé à la racine du projet Django (`plateformeSIG/`). Voir
[`.env.example`](plateformeSIG/.env.example) :

| Variable | Description | Défaut |
|---|---|---|
| `DB_NAME` | Nom de la base PostgreSQL | `plateformeSIG` |
| `DB_USER` | Utilisateur PostgreSQL | `postgres` |
| `DB_PASSWORD` | Mot de passe | *(vide)* |
| `DB_HOST` / `DB_PORT` | Hôte / port | `localhost` / `5432` |
| `DJANGO_SECRET_KEY` | Clé secrète Django | clé de dev (à changer) |
| `DJANGO_DEBUG` | Mode debug (`True`/`False`) | `True` |
| `DJANGO_ALLOWED_HOSTS` | Hôtes autorisés (séparés par virgules) | *(vide)* |

## Tests

```bash
cd plateformeSIG
python manage.py test
```

## Notes

- Tous les tableaux mensuels suivent le calendrier hydrologique **septembre → août**.
- Les géométries sont stockées en **SRID 4326** ; les coordonnées brutes sont en
  Nord Maroc (**EPSG:26191**).
- Le gating des rôles est actuellement côté template uniquement — à renforcer côté vues
  avant une mise en production.
