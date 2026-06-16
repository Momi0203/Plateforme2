"""
Commande : python manage.py import_reseau_guir [--replace]

Module INDÉPENDANT d'import du réseau hydrographique « ouvrage de tête » du
bassin Guir, lu depuis :
  plateformeSIG/plateformeSIG/static/resaux hydrographique ouvrage en tete/guir.shp

Insère les tronçons (LineString) dans le modèle carte.ReseauOuvrageTeteGuir.
Forme du modèle : grid_code + geometrie (aucune clé étrangère).

NB : le shapefile guir.shp n'est pas encore présent dans le dossier — déposez-le
puis lancez la commande (usage ultérieur).

Mapping des champs SHP -> modèle :
  grid_code <- grid_code   (alias : grid_code / gridcode / sorder / strahler / arcid)
"""
from pathlib import Path

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiLineString
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from carte.models import ReseauOuvrageTeteGuir

BATCH_SIZE = 2000

# Dossier des réseaux hydrographiques / ouvrages en tête (relatif à BASE_DIR)
RESEAU_DIR_REL = Path("plateformeSIG") / "static" / "resaux hydrographique ouvrage en tete"

# Paramètres propres à ce module
MODELE        = ReseauOuvrageTeteGuir
SHP_CANDIDATS = ["guir", "Guir"]   # noms de fichier .shp essayés, dans l'ordre
ALIAS_GRID    = ["grid_code", "gridcode", "grid", "sorder", "strahler", "arcid"]


def _trouver_shp(reseau_dir, candidats):
    """Premier .shp existant parmi les candidats, ou None."""
    for nom in candidats:
        p = reseau_dir / (nom + ".shp")
        if p.exists():
            return p
    return None


def _trouver_champ(layer, alias):
    """Nom réel du premier champ de `layer` correspondant à un alias
    (comparaison insensible à la casse), ou None."""
    dispo = {f.lower(): f for f in layer.fields}
    for a in alias:
        if a.lower() in dispo:
            return dispo[a.lower()]
    return None


class Command(BaseCommand):
    help = "Importe le réseau hydrographique (ouvrage de tête) du bassin Guir."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Vide la table du modèle avant import.",
        )

    def handle(self, *args, **opts):
        reseau_dir = Path(settings.BASE_DIR) / RESEAU_DIR_REL
        shp_path = _trouver_shp(reseau_dir, SHP_CANDIDATS)
        if shp_path is None:
            raise CommandError(
                f"Shapefile introuvable dans : {reseau_dir}\n"
                f"Noms essayés : {[c + '.shp' for c in SHP_CANDIDATS]}"
            )

        ds = DataSource(str(shp_path))
        layer = ds[0]
        total = len(layer)
        srid_src = layer.srs.srid if layer.srs else None
        f_grid = _trouver_champ(layer, ALIAS_GRID)

        self.stdout.write(f"Source   : {shp_path}")
        self.stdout.write(f"Modèle   : carte.{MODELE.__name__}")
        self.stdout.write(f"Tronçons : {total}   SRID source : {srid_src}")
        self.stdout.write(f"Champs   : grid_code <- {f_grid or '(NULL)'}")

        with transaction.atomic():
            if opts["replace"]:
                deleted, _ = MODELE.objects.all().delete()
                self.stdout.write(self.style.WARNING(f"Table vidée ({deleted} ligne(s))."))

            batch, inserted, skipped = [], 0, 0

            for i, feat in enumerate(layer, start=1):
                geom = feat.geom
                if geom is None or geom.empty:
                    skipped += 1
                    continue
                if srid_src and srid_src != 4326:
                    geom.transform(4326)

                grid_code = None
                if f_grid:
                    try:
                        grid_code = int(feat.get(f_grid))
                    except (TypeError, ValueError):
                        grid_code = None

                geos = GEOSGeometry(geom.wkb, srid=4326)
                parts = list(geos) if isinstance(geos, MultiLineString) else [geos]
                for part in parts:
                    if part.empty:
                        continue
                    batch.append(MODELE(grid_code=grid_code, geometrie=part))

                if len(batch) >= BATCH_SIZE:
                    MODELE.objects.bulk_create(batch, batch_size=BATCH_SIZE)
                    inserted += len(batch)
                    batch = []
                    self.stdout.write(f"  {i}/{total} traités — {inserted} insérés…")

            if batch:
                MODELE.objects.bulk_create(batch, batch_size=BATCH_SIZE)
                inserted += len(batch)

        self.stdout.write(self.style.SUCCESS(
            f"Terminé : {inserted} tronçon(s) inséré(s), {skipped} ignoré(s)."
        ))
