# Déploiement sur Render (PostgreSQL + PostGIS)

Ce guide déploie la plateforme SIG sur [Render](https://render.com) via **Docker**
(nécessaire pour les bibliothèques natives GDAL / GEOS / PROJ de GeoDjango).

> **Pourquoi pas PythonAnywhere ?** PythonAnywhere ne fournit pas l'extension
> **PostGIS**, indispensable ici (champs géométriques), et l'app utilise des
> `ArrayField` PostgreSQL. Render fournit PostgreSQL avec PostGIS → aucun
> refactoring nécessaire.

## Fichiers déjà préparés dans le dépôt

| Fichier | Rôle |
|---|---|
| `Dockerfile` | Image Python 3.13 + GDAL/GEOS/PROJ + Gunicorn ; migre et collecte les statiques |
| `.dockerignore` | Exclut venv, db, media, docs du contexte de build |
| `render.yaml` | Blueprint Render (base + service web + variables) |
| `requirements.txt` | + `gunicorn`, `whitenoise`, `dj-database-url` |
| `settings.py` | Lit `DATABASE_URL`, chemins GIS conditionnés à Windows, WhiteNoise, sécurité HTTPS |

---

## Option A — Déploiement automatique via Blueprint (recommandé)

1. **Crée un compte** sur https://render.com (connexion avec GitHub).
2. Dashboard → **New +** → **Blueprint**.
3. Sélectionne le dépôt **`Momi0203/Plateforme2`**. Render lit `render.yaml` et
   propose de créer **1 base PostgreSQL** + **1 service web Docker**. Clique **Apply**.
4. Attends la fin de la création de la base (statut *Available*).
5. **Active PostGIS** (une seule fois) — voir la section ci-dessous.
6. Le service web se construit (build Docker ~5-10 min). À la fin il est accessible sur
   `https://plateformesig.onrender.com`.

---

## Option B — Déploiement manuel (sans render.yaml)

### 1. Créer la base de données
- **New +** → **PostgreSQL** → Name `plateformesig-db`, Plan **Free**, Version **16** → **Create**.
- Attends *Available*.

### 2. Activer PostGIS (obligatoire, une fois)
Sur la page de la base, section **Connect**, copie la **PSQL Command** et lance-la dans
un terminal où `psql` est installé (ou via le bouton **Connect ▸ External Connection**) :

```bash
psql "postgresql://...la chaîne fournie par Render..."
```
Puis dans psql :
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
\q
```

### 3. Créer le service web
- **New +** → **Web Service** → connecte le dépôt `Momi0203/Plateforme2`.
- **Language / Runtime** : **Docker** (Render détecte le `Dockerfile`).
- **Plan** : Free.
- **Environment Variables** (section *Advanced* / *Environment*) :

| Clé | Valeur |
|---|---|
| `DATABASE_URL` | l'**Internal Database URL** de la base créée |
| `DJANGO_SECRET_KEY` | une clé aléatoire (bouton *Generate* ou commande ci-dessous) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://<nom-du-service>.onrender.com` |

Générer une clé secrète :
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

- **Create Web Service**. Le build Docker démarre ; au lancement le conteneur
  applique les migrations (`migrate`) puis démarre Gunicorn.

---

## Créer un compte administrateur

Le `Dockerfile` applique les migrations automatiquement, mais pas le superutilisateur.
Deux options :

**Via le Shell Render** (onglet *Shell* du service web) :
```bash
python manage.py createsuperuser
```

**Sinon** (si le Shell n'est pas disponible sur le plan Free), ajoute temporairement
ces variables d'environnement puis relance un déploiement avec, en *Pre-Deploy Command* :
```bash
python manage.py createsuperuser --noinput
```
avec `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`.
Retire-les ensuite.

---

## Charger les données

La base Render démarre vide. Pour réimporter tes données :
- Commandes d'import du projet (shapefiles), ex. `python manage.py import_mibladen`,
  `import_reseau_ziz`, etc., via le Shell Render.
- Ou un dump/restore depuis ta base locale (`pg_dump` → `psql`), **après** avoir
  activé PostGIS sur la base Render.

---

## Limitations du plan gratuit Render

- Le service web **s'endort** après 15 min d'inactivité (premier accès ensuite ~30 s).
- La base PostgreSQL gratuite **expire après ~30 jours** (sauvegarde/migration requise).
- Le **système de fichiers est éphémère** : les uploads dans `media/` sont perdus à
  chaque redéploiement. Pour les conserver, utiliser un stockage externe (S3, etc.).

---

## Vérifier en local avec Docker (optionnel)

```bash
# Depuis la racine du dépôt
docker build -t plateformesig .
docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e DATABASE_URL="postgis://user:pass@host:5432/dbname" \
  -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1" \
  plateformesig
```
