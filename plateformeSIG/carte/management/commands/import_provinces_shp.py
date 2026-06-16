import os
from decimal import Decimal

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, LinearRing, MultiPolygon, Polygon
from django.core.management.base import BaseCommand
from django.db import transaction

from carte.models import Province


SHP_DEFAULT_PATH = os.path.join(
    settings.BASE_DIR, 'plateformeSIG', 'static', 'decoupage admistratif',
    'provinces', 'provinces_tafilalt.shp'
)

FIELD_MAP = {
    'nom_fr': 'nom_fr',
    'nom_ar': 'nom_ar',
    'annee_refe': 'annee_refe',
    'population': 'population_totale',
    'populati_1': 'population_urbaine',
    'populati_2': 'population_rurale',
    'nombre_men': 'nombre_menages',
    'superficie': 'superficie_km2',
    'densite_ha': 'densite_hab_km2',
    'taux_urban': 'taux_urbanisation_pct',
    'taux_accro': 'taux_accroissement_pct',
    'communes_u': 'communes_urbaines',
    'communes_r': 'communes_rurales',
    'station_me': 'station_meteo',
    'temp_moy_a': 'temp_moy_annuelle_c',
    'precip_ann': 'precip_annuelle_mm',
    'humidite_r': 'humidite_rel_moy_pct',
    'et0_moy_jo': 'et0_moy_journaliere_mm_j',
    'et0_annuel': 'et0_annuelle_mm',
}

INT_FIELDS = {
    'annee_refe',
    'population_totale',
    'population_urbaine',
    'population_rurale',
    'nombre_menages',
    'communes_urbaines',
    'communes_rurales',
}

DECIMAL_FIELDS = {
    'superficie_km2',
    'densite_hab_km2',
    'taux_urbanisation_pct',
    'taux_accroissement_pct',
    'temp_moy_annuelle_c',
    'precip_annuelle_mm',
    'humidite_rel_moy_pct',
    'et0_moy_journaliere_mm_j',
    'et0_annuelle_mm',
}


def _to_2d_polygon(geom):
    """Convertit une géométrie Polygon/MultiPolygon en 2D (SRID 4326)."""
    if geom.srid != 4326:
        geom.transform(4326)

    if not geom.hasz:
        return geom

    if geom.geom_type == 'Polygon':
        ext = [(x, y) for x, y, *_ in geom.exterior_ring.coords]
        ints = [[(x, y) for x, y, *_ in r.coords] for r in geom.interior_rings]
        return Polygon(LinearRing(ext), *ints, srid=4326)

    if geom.geom_type == 'MultiPolygon':
        polys = []
        for poly in geom:
            ext = [(x, y) for x, y, *_ in poly.exterior_ring.coords]
            ints = [[(x, y) for x, y, *_ in r.coords] for r in poly.interior_rings]
            polys.append(Polygon(LinearRing(ext), *ints, srid=4326))
        return MultiPolygon(*polys, srid=4326)

    return geom


def _coerce(field_name, value):
    if value is None or value == '':
        return None
    if field_name in INT_FIELDS:
        return int(round(float(value)))
    if field_name in DECIMAL_FIELDS:
        return Decimal(str(value))
    return value


class Command(BaseCommand):
    help = "Importe les provinces du Tafilalet depuis le shapefile fourni."

    def add_arguments(self, parser):
        parser.add_argument(
            '--path', default=SHP_DEFAULT_PATH,
            help="Chemin vers le fichier .shp (par défaut : static/decoupage admistratif/provinces/provinces_tafilalt.shp)",
        )
        parser.add_argument(
            '--update', action='store_true',
            help="Met à jour les provinces existantes (matching sur nom_fr) au lieu de les ignorer.",
        )
        parser.add_argument(
            '--purge', action='store_true',
            help="Supprime toutes les provinces avant l'import.",
        )

    def handle(self, *args, **options):
        shp_path = options['path']
        if not os.path.exists(shp_path):
            self.stderr.write(self.style.ERROR(f"Shapefile introuvable : {shp_path}"))
            return

        self.stdout.write(f"Lecture du shapefile : {shp_path}")
        ds = DataSource(shp_path)
        layer = ds[0]

        if options['purge']:
            count = Province.objects.count()
            Province.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"{count} province(s) supprimée(s)."))

        created, updated, skipped = 0, 0, 0

        with transaction.atomic():
            for idx, feat in enumerate(layer, start=1):
                try:
                    fields = {name: feat.get(name) for name in feat.fields}

                    data = {}
                    for shp_field, model_field in FIELD_MAP.items():
                        if shp_field in fields:
                            data[model_field] = _coerce(model_field, fields[shp_field])

                    nom_fr = data.get('nom_fr')
                    if not nom_fr:
                        self.stderr.write(f"  Forme {idx} ignorée : nom_fr manquant.")
                        skipped += 1
                        continue

                    geom = GEOSGeometry(feat.geom.wkt, srid=feat.geom.srid or 4326)
                    geom = _to_2d_polygon(geom)

                    # Le modèle utilise PolygonField : si MultiPolygon à un seul polygone, on extrait
                    if geom.geom_type == 'MultiPolygon' and len(geom) == 1:
                        geom = geom[0]

                    if geom.geom_type != 'Polygon':
                        self.stderr.write(
                            f"  Forme {idx} ({nom_fr}) ignorée : géométrie {geom.geom_type} "
                            f"non compatible avec PolygonField."
                        )
                        skipped += 1
                        continue

                    data['geometrie'] = geom

                    existing = Province.objects.filter(nom_fr=nom_fr).first()
                    if existing:
                        if options['update']:
                            for k, v in data.items():
                                setattr(existing, k, v)
                            existing.save()
                            updated += 1
                            self.stdout.write(f"  Mis à jour : {nom_fr}")
                        else:
                            skipped += 1
                            self.stdout.write(f"  Déjà existant, ignoré : {nom_fr}")
                    else:
                        Province.objects.create(**data)
                        created += 1
                        self.stdout.write(self.style.SUCCESS(f"  Créé : {nom_fr}"))

                except Exception as exc:
                    skipped += 1
                    self.stderr.write(self.style.ERROR(f"  Forme {idx} : erreur {exc}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nImport terminé : {created} créée(s), {updated} mise(s) à jour, {skipped} ignorée(s)."
        ))
