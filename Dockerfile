# syntax=docker/dockerfile:1
# Image de déploiement pour la plateforme SIG (Django 6 + GeoDjango / PostGIS).
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_DEBUG=False

# Bibliothèques natives GIS (GDAL / GEOS / PROJ) + dépendances de compilation de psycopg2.
RUN apt-get update && apt-get install -y --no-install-recommends \
        binutils \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dépendances Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Code du projet Django (dossier interne plateformeSIG/ qui contient manage.py).
COPY plateformeSIG/ /app/

# Génère les fichiers statiques (collectés dans STATIC_ROOT, servis par WhiteNoise).
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Applique les migrations au démarrage, puis lance Gunicorn.
# ${PORT} est fourni par l'hébergeur (Render/Railway), 8000 par défaut en local.
CMD python manage.py migrate --noinput && \
    gunicorn plateformeSIG.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers 3 \
        --timeout 120
