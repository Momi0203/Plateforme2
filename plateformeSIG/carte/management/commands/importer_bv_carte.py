"""
Commande : python manage.py importer_bv_carte [--replace]

Insère les 5 bassins versants et leurs réseaux hydrographiques dans les modèles
carte.BassinVersant et carte.ReseauHydrographique, en lisant :
  - plateformeSIG/static/bassin versant/bv plateforme.xlsx  (attributs)
  - plateformeSIG/static/bassin versant/<nom>.shp            (polygone BV)
  - plateformeSIG/static/bassin versant/rivers <nom>.shp     (réseau hydrographique)

Conversions :
  - Périmètre calculé depuis la géométrie SHP reprojetée en EPSG:26191
"""
from pathlib import Path

import openpyxl
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, MultiLineString, Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from carte.models import BassinVersant, ReseauHydrographique

BATCH_SIZE = 500

BV_DIR_REL = Path("plateformeSIG") / "static" / "bassin versant"

# Mapping complet : nom BV en base → noms de fichiers SHP + clé Excel
BV_CONFIG = [
    {
        "nom":        "Guir",
        "shp_bv":     "Guir",
        "shp_rivers": "rivers Guir",
        "excel_key":  "Guir",
    },
    {
        "nom":        "Moulouya",
        "shp_bv":     "Moulouya",
        "shp_rivers": "rivers Moulouya",
        "excel_key":  "Moulouya",
    },
    {
        "nom":        "Rhéris",
        "shp_bv":     "Rheris",
        "shp_rivers": "rivers Rheris",
        "excel_key":  "Rhéris",
    },
    {
        "nom":        "Maïder",
        "shp_bv":     "Madier",
        "shp_rivers": "rivers Maider",
        "excel_key":  "Maider",
    },
    {
        "nom":        "Ziz",
        "shp_bv":     "Ziz",
        "shp_rivers": "rivers ziz",
        "excel_key":  "Ziz",
    },
]

# Colonnes de la feuille Excel (index 0-based)
COL_NOM       = 0
COL_EXUTOIRE  = 1   # "lat, lon"
COL_SURFACE   = 2   # Superficie (km²)
COL_THALWEG   = 13  # Longueur plus long cours d'eau (km)
COL_ALT_SRC   = 14  # Altitude source (m)
COL_ALT_EXU   = 15  # Altitude exutoire (m)
COL_ALT_MIN   = 16  # Altitude minimale (m)
COL_ALT_MOY   = 17  # Altitude moyenne (m)
COL_ALT_MAX   = 18  # Altitude maximale (m)
COL_PRECIP    = 9   # Précipitations annuelles (mm/an)
COL_ETP       = 10  # Évapotranspiration annuelle (mm/an)


def _lire_excel(xlsx_path):
    """
    Retourne un dict { nom_excel : {superficie_km2, thalweg_km, altitude_min,
    altitude_max, altitude_exutoire, precip, etp} }.
    """
    wb = openpyxl.load_workbook(str(xlsx_path), data_only=True)
    ws = wb["Feuil2"]
    data = {}
    for row in list(ws.iter_rows(values_only=True))[1:]:
        if row[COL_NOM] is None:
            continue
        nom = str(row[COL_NOM]).strip()

        def _f(col):
            v = row[col]
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        data[nom] = {
            "superficie_km2":    _f(COL_SURFACE),
            "thalweg_km":        _f(COL_THALWEG),
            "altitude_min":      _f(COL_ALT_MIN),
            "altitude_max":      _f(COL_ALT_MAX),
            "altitude_exutoire": _f(COL_ALT_EXU),
            "precip":            _f(COL_PRECIP),
            "etp":               _f(COL_ETP),
        }
    return data


def _perimetre_km(geom_4326):
    """Périmètre (km) d'un polygone WGS84 calculé via reprojection EPSG:26191."""
    geom_m = geom_4326.transform(26191, clone=True)
    return geom_m.length / 1000.0


class Command(BaseCommand):
    help = "Importe les 5 BV et leurs réseaux hydrographiques dans carte.BassinVersant / carte.ReseauHydrographique."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Supprime les enregistrements existants (même nom) avant import.",
        )

    def handle(self, *args, **opts):
        bv_dir = Path(settings.BASE_DIR) / BV_DIR_REL
        if not bv_dir.exists():
            raise CommandError(f"Dossier introuvable : {bv_dir}")

        xlsx = bv_dir / "bv plateforme.xlsx"
        if not xlsx.exists():
            raise CommandError(f"Fichier Excel introuvable : {xlsx}")

        self.stdout.write(f"Source : {bv_dir}\n")
        excel = _lire_excel(xlsx)
        self.stdout.write(f"Excel : {len(excel)} BV -> {list(excel.keys())}\n")

        with transaction.atomic():
            for cfg in BV_CONFIG:
                nom       = cfg["nom"]
                key       = cfg["excel_key"]
                shp_bv    = bv_dir / (cfg["shp_bv"] + ".shp")
                shp_riv   = bv_dir / (cfg["shp_rivers"] + ".shp")

                # ── BassinVersant ──────────────────────────────────────────────
                self.stdout.write(f"\n{'─'*55}")
                self.stdout.write(f" BassinVersant : {nom}")

                if not shp_bv.exists():
                    self.stdout.write(self.style.WARNING(f"  SHP absent : {shp_bv} — ignoré."))
                    continue

                # Lookup Excel avec fallback insensible aux accents
                attrs = excel.get(key)
                if attrs is None:
                    for k, v in excel.items():
                        if k.lower().replace("é","e").replace("ï","i") == key.lower().replace("é","e").replace("ï","i"):
                            attrs = v
                            break
                if attrs is None:
                    self.stdout.write(self.style.WARNING(f"  Données Excel manquantes pour '{key}' — ignoré."))
                    continue

                if opts["replace"]:
                    n, _ = BassinVersant.objects.filter(nom=nom).delete()
                    if n:
                        self.stdout.write(self.style.WARNING(f"  {n} enregistrement(s) supprimé(s)."))

                # Géométrie
                ds    = DataSource(str(shp_bv))
                layer = ds[0]
                feat  = layer[0]
                geom  = GEOSGeometry(feat.geom.wkb, srid=4326)
                if isinstance(geom, MultiPolygon):
                    geom = geom[0]

                perim_km = _perimetre_km(geom)

                bv_obj = BassinVersant(
                    nom=nom,
                    superficie_km2=attrs["superficie_km2"] or 0.0,
                    perimetre_km=round(perim_km, 2),
                    altitude_min=attrs["altitude_min"] or 0.0,
                    altitude_max=attrs["altitude_max"] or 0.0,
                    altitude_exutoire=attrs["altitude_exutoire"] or 0.0,
                    thalweg_km=attrs["thalweg_km"] or 0.0,
                    precipitations_annuelles_mm=attrs["precip"],
                    evapotranspiration_annuelle_mm=attrs["etp"],
                    geometrie=geom,
                )
                bv_obj.save()
                self.stdout.write(self.style.SUCCESS(
                    f"  OK BassinVersant id={bv_obj.pk} - "
                    f"superficie={attrs['superficie_km2']} km2  "
                    f"perimetre~{perim_km:.1f} km  "
                    f"alt[{attrs['altitude_min']}..{attrs['altitude_max']}] m"
                ))

                # ── ReseauHydrographique ───────────────────────────────────────
                self.stdout.write(f" Réseau hydrographique : {cfg['shp_rivers']}.shp")

                if not shp_riv.exists():
                    self.stdout.write(self.style.WARNING(f"  SHP absent : {shp_riv} — réseau ignoré."))
                    continue

                ds_r    = DataSource(str(shp_riv))
                layer_r = ds_r[0]
                total   = len(layer_r)
                self.stdout.write(f"  {total} tronçons à importer…")

                batch    = []
                inserted = 0
                skipped  = 0

                for feat_r in layer_r:
                    try:
                        comid  = int(feat_r.get("comid"))
                        sorder = int(feat_r.get("sorder"))
                    except Exception:
                        comid  = 0
                        sorder = 0

                    geom_r = feat_r.geom
                    if geom_r is None or geom_r.empty:
                        skipped += 1
                        continue

                    if layer_r.srs and layer_r.srs.srid and layer_r.srs.srid != 4326:
                        geom_r.transform(4326)

                    geos_r = GEOSGeometry(geom_r.wkb, srid=4326)
                    parts  = list(geos_r) if isinstance(geos_r, MultiLineString) else [geos_r]

                    for part in parts:
                        if part.empty:
                            continue
                        batch.append(ReseauHydrographique(
                            bassin_versant=bv_obj,
                            comid=comid,
                            sorder=sorder,
                            geometrie=part,
                        ))

                    if len(batch) >= BATCH_SIZE:
                        ReseauHydrographique.objects.bulk_create(batch, batch_size=BATCH_SIZE)
                        inserted += len(batch)
                        batch = []

                if batch:
                    ReseauHydrographique.objects.bulk_create(batch, batch_size=BATCH_SIZE)
                    inserted += len(batch)

                self.stdout.write(self.style.SUCCESS(
                    f"  OK {inserted} troncons inseres  ({skipped} ignores)"
                ))

        self.stdout.write(self.style.SUCCESS("\nImport termine avec succes."))
