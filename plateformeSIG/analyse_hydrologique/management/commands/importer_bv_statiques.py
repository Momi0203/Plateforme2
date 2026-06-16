"""
Commande : python manage.py importer_bv_statiques [--replace] [--bv-seulement] [--rivers-seulement]

Importe les 5 bassins versants et leurs réseaux hydrographiques depuis
  plateformeSIG/plateformeSIG/static/bassin versant/

Sources :
  - bv plateforme.xlsx  → attributs (superficie, altitudes, thalweg, coordonnées exutoire)
  - Guir/Ziz/Rheris/Madier/Moulouya.shp     → géométries polygone (1 feature / BV)
  - rivers Guir/ziz/Rheris/Maider/Moulouya.shp → réseaux hydrographiques (LineString)

Conversions :
  - Exutoire (lat, lon WGS84) converti en EPSG:26191 (Nord Maroc, m)
  - Périmètre calculé depuis la géométrie SHP reprojetée en 26191
"""
from pathlib import Path

import openpyxl
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, MultiLineString, Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from analyse_hydrologique.models import BassinVersant

BATCH_SIZE = 500

# Dossier contenant les shapefiles (relatif à BASE_DIR du projet Django)
BV_DIR_REL = Path("plateformeSIG") / "static" / "bassin versant"

# Mapping : clé = nom du BV dans la base, valeurs = noms de fichiers SHP
# (sans extension, sensibles à la casse du disque)
BV_CONFIG = [
    {
        "nom": "Guir",
        "shp_bv": "Guir",
        "shp_rivers": "rivers Guir",
        "col_excel": "Guir",
    },
    {
        "nom": "Moulouya",
        "shp_bv": "Moulouya",
        "shp_rivers": "rivers Moulouya",
        "col_excel": "Moulouya",
    },
    {
        "nom": "Rhéris",
        "shp_bv": "Rheris",
        "shp_rivers": "rivers Rheris",
        "col_excel": "Rhéris",
    },
    {
        "nom": "Maïder",
        "shp_bv": "Madier",
        "shp_rivers": "rivers Maider",
        "col_excel": "Maider",
    },
    {
        "nom": "Ziz",
        "shp_bv": "Ziz",
        "shp_rivers": "rivers ziz",
        "col_excel": "Ziz",
    },
]


def _lire_excel(xlsx_path):
    """
    Retourne un dict  nom_excel → {surface, thalweg, z_min, z_max, lat, lon}
    depuis la feuille 'Feuil2' du classeur.
    """
    wb = openpyxl.load_workbook(str(xlsx_path), data_only=True)
    ws = wb["Feuil2"]
    rows = list(ws.iter_rows(values_only=True))

    data = {}
    for row in rows[1:]:          # ligne 0 = en-têtes
        if row[0] is None:
            continue
        nom = str(row[0]).strip()
        lat_lon_str = str(row[1]).strip()   # "31.916, -3.091"
        lat, lon = [float(v.strip()) for v in lat_lon_str.split(",")]

        surface = float(row[2]) if row[2] is not None else 0.0
        thalweg = float(row[13]) if row[13] is not None else 0.0
        z_min   = float(row[16]) if row[16] is not None else 0.0
        z_max   = float(row[18]) if row[18] is not None else 0.0

        data[nom] = {
            "lat": lat, "lon": lon,
            "surface": surface,
            "thalweg": thalweg,
            "z_min": z_min,
            "z_max": z_max,
        }
    return data


def _lat_lon_to_nord_maroc(lat, lon):
    """
    Convertit (lat, lon) WGS84 en (x, y) EPSG:26191 (Lambert Nord Maroc, m).
    Retourne (x_m, y_m).
    """
    pt = Point(lon, lat, srid=4326)   # GEOS : (x=lon, y=lat)
    pt.transform(26191)
    return pt.x, pt.y


def _perimetre_km(geom_4326):
    """
    Calcule le périmètre (km) d'un polygone WGS84 en le reprojetant en 26191.
    """
    geom_m = geom_4326.transform(26191, clone=True)
    return geom_m.length / 1000.0


class Command(BaseCommand):
    help = "Importe les 5 BV statiques et leurs réseaux hydrographiques."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Supprime les enregistrements existants portant le même nom avant import.",
        )

    def handle(self, *args, **opts):
        bv_dir = Path(settings.BASE_DIR) / BV_DIR_REL
        if not bv_dir.exists():
            raise CommandError(f"Dossier introuvable : {bv_dir}")

        xlsx_path = bv_dir / "bv plateforme.xlsx"
        if not xlsx_path.exists():
            raise CommandError(f"Fichier Excel introuvable : {xlsx_path}")

        self.stdout.write(f"Dossier source : {bv_dir}")

        # --- Lecture Excel ---
        self.stdout.write("Lecture du classeur Excel…")
        excel_data = _lire_excel(xlsx_path)
        self.stdout.write(f"  {len(excel_data)} bassins versants trouvés : {list(excel_data.keys())}")

        do_bv = True

        with transaction.atomic():
            for cfg in BV_CONFIG:
                nom_bv    = cfg["nom"]
                nom_excel = cfg["col_excel"]
                shp_bv    = bv_dir / (cfg["shp_bv"] + ".shp")
                shp_riv   = bv_dir / (cfg["shp_rivers"] + ".shp")

                # ──────────────── BV ────────────────
                if do_bv:
                    self.stdout.write(f"\n[BV] {nom_bv}")
                    if not shp_bv.exists():
                        self.stdout.write(self.style.WARNING(f"  SHP absent : {shp_bv} — ignoré."))
                    elif nom_excel not in excel_data:
                        self.stdout.write(self.style.WARNING(f"  Données Excel manquantes pour '{nom_excel}' — ignoré."))
                    else:
                        attrs = excel_data[nom_excel]

                        if opts["replace"]:
                            deleted, _ = BassinVersant.objects.filter(nom=nom_bv).delete()
                            if deleted:
                                self.stdout.write(self.style.WARNING(f"  {deleted} enregistrement(s) supprimé(s)."))

                        # Géométrie polygone
                        ds    = DataSource(str(shp_bv))
                        layer = ds[0]
                        feat  = layer[0]
                        geom  = GEOSGeometry(feat.geom.wkb, srid=4326)
                        if isinstance(geom, MultiPolygon):
                            geom = geom[0]   # prendre le premier polygone

                        # Coordonnées exutoire → Nord Maroc
                        x_m, y_m = _lat_lon_to_nord_maroc(attrs["lat"], attrs["lon"])

                        # Périmètre calculé depuis la géométrie
                        perim_km = _perimetre_km(geom)

                        bv_obj = BassinVersant(
                            nom=nom_bv,
                            x_exutoire=x_m,
                            y_exutoire=y_m,
                            surface=attrs["surface"],
                            perimetre=round(perim_km, 2),
                            z_min=attrs["z_min"],
                            z_max=attrs["z_max"],
                            thalweg=attrs["thalweg"],
                            geometrie=geom,
                        )
                        bv_obj.save()
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✓ BassinVersant '{nom_bv}' créé (id={bv_obj.pk}, "
                            f"surface={attrs['surface']} km², périmètre≈{perim_km:.1f} km)"
                        ))

        self.stdout.write(self.style.SUCCESS("\nImport terminé."))
