import os
from decimal import Decimal

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, LinearRing, MultiPolygon, Polygon
from django.core.management.base import BaseCommand
from django.db import transaction

from carte.models import Commune, Province


SHP_DEFAULT_PATH = os.path.join(
    settings.BASE_DIR, 'plateformeSIG', 'static', 'decoupage admistratif',
    'commune_errachidia', 'commune_er_29.shp'
)

ANNEE_REFE_DEFAULT = 2004
PROVINCE_NOM = 'Errachidia'

FIELD_MAP = {
    'nom_fr': ['nom_fr'],
    'nom_ar': ['nom_ar'],
    'type_commune': ['type_commu'],
    'population_totale': ['populati_1', 'population', 'P_ensemble'],
    'nombre_menages': ['menages_20', 'P_menages'],
    'superficie_km2': ['s'],
    'station_meteo': ['station_me'],
    'temp_moy_annuelle_c': ['temp_moy_a'],
    'precip_annuelle_mm': ['precip_ann'],
    'humidite_rel_moy_pct': ['humidite_r'],
    'et0_moy_journaliere_mm_j': ['et0_moy_jo'],
    'et0_annuelle_mm': ['et0_annuel'],
}

INT_FIELDS = {
    'population_totale',
    'nombre_menages',
}

DECIMAL_FIELDS = {
    'superficie_km2',
    'temp_moy_annuelle_c',
    'precip_annuelle_mm',
    'humidite_rel_moy_pct',
    'et0_moy_journaliere_mm_j',
    'et0_annuelle_mm',
}


def _normalize_type(value):
    if value is None:
        return None
    s = str(value).strip().lower()
    if s.startswith('urb'):
        return 'Urbaine'
    if s.startswith('rur'):
        return 'Rurale'
    return None


def _to_2d_polygon(geom):
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
    if field_name == 'type_commune':
        return _normalize_type(value)
    if field_name in INT_FIELDS:
        return int(round(float(value)))
    if field_name == 'superficie_km2':
        # Le champ SHP `s` est en m^2 -> conversion en km^2
        return (Decimal(str(value)) / Decimal('1000000')).quantize(Decimal('0.01'))
    if field_name in DECIMAL_FIELDS:
        return Decimal(str(value))
    return value


class Command(BaseCommand):
    help = "Importe les 29 communes d'Errachidia depuis le shapefile fourni."

    def add_arguments(self, parser):
        parser.add_argument('--path', default=SHP_DEFAULT_PATH)
        parser.add_argument('--annee', type=int, default=ANNEE_REFE_DEFAULT)
        parser.add_argument('--province', default=PROVINCE_NOM)
        parser.add_argument('--update', action='store_true',
                            help="Met à jour les communes existantes (match sur nom_fr).")
        parser.add_argument('--purge', action='store_true',
                            help="Supprime toutes les communes de la province avant import.")

    def handle(self, *args, **options):
        shp_path = options['path']
        if not os.path.exists(shp_path):
            self.stderr.write(self.style.ERROR(f"Shapefile introuvable : {shp_path}"))
            return

        try:
            province = Province.objects.get(nom_fr=options['province'])
        except Province.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f"Province '{options['province']}' introuvable. Importer d'abord les provinces."
            ))
            return

        self.stdout.write(f"Lecture du shapefile : {shp_path}")
        self.stdout.write(f"Province cible : {province.nom_fr} (annee_refe={options['annee']})")

        ds = DataSource(shp_path)
        layer = ds[0]

        if options['purge']:
            count = Commune.objects.filter(province=province).count()
            Commune.objects.filter(province=province).delete()
            self.stdout.write(self.style.WARNING(f"{count} commune(s) supprimée(s) de {province.nom_fr}."))

        # Valeurs de repli depuis la province (pour les champs SHP à NULL)
        fallback = {
            'station_meteo': province.station_meteo,
            'temp_moy_annuelle_c': province.temp_moy_annuelle_c,
            'precip_annuelle_mm': province.precip_annuelle_mm,
            'humidite_rel_moy_pct': province.humidite_rel_moy_pct,
            'et0_moy_journaliere_mm_j': province.et0_moy_journaliere_mm_j,
            'et0_annuelle_mm': province.et0_annuelle_mm,
        }

        created, updated, skipped = 0, 0, 0

        for idx, feat in enumerate(layer, start=1):
            try:
                with transaction.atomic():
                    fields = {name: feat.get(name) for name in feat.fields}

                    data = {'province': province, 'annee_refe': options['annee']}
                    for model_field, shp_aliases in FIELD_MAP.items():
                        for shp_field in shp_aliases:
                            if shp_field in fields and fields[shp_field] not in (None, ''):
                                data[model_field] = _coerce(model_field, fields[shp_field])
                                break

                    # Repli sur les valeurs de la province pour les champs NOT NULL
                    for fname, fval in fallback.items():
                        if data.get(fname) in (None, ''):
                            data[fname] = fval

                    nom_fr = data.get('nom_fr')
                    if not nom_fr:
                        self.stderr.write(f"  Forme {idx} ignorée : nom_fr manquant.")
                        skipped += 1
                        continue

                    if not data.get('type_commune'):
                        self.stderr.write(
                            f"  Forme {idx} ({nom_fr}) : type_commune non reconnu "
                            f"('{fields.get('type_commu')}') — défaut 'Rurale'."
                        )
                        data['type_commune'] = 'Rurale'

                    geom = GEOSGeometry(feat.geom.wkt, srid=feat.geom.srid or 4326)
                    geom = _to_2d_polygon(geom)

                    # PolygonField : si MultiPolygon → garder le plus grand polygone
                    if geom.geom_type == 'MultiPolygon':
                        if len(geom) == 1:
                            geom = geom[0]
                        else:
                            largest = max(geom, key=lambda p: p.area)
                            self.stdout.write(
                                f"  Forme {idx} ({nom_fr}) : MultiPolygon a {len(geom)} parties; "
                                f"plus grand polygone conserve (aire {largest.area:.6f})."
                            )
                            geom = largest

                    if geom.geom_type != 'Polygon':
                        self.stderr.write(
                            f"  Forme {idx} ({nom_fr}) ignorée : géométrie {geom.geom_type}."
                        )
                        skipped += 1
                        continue
                    data['geometrie'] = geom

                    existing = Commune.objects.filter(nom_fr=nom_fr).first()
                    if existing:
                        if options['update']:
                            for k, v in data.items():
                                setattr(existing, k, v)
                            existing.save()
                            updated += 1
                            self.stdout.write(f"  Mise à jour : {nom_fr}")
                        else:
                            skipped += 1
                            self.stdout.write(f"  Déjà existante, ignorée : {nom_fr}")
                    else:
                        Commune.objects.create(**data)
                        created += 1
                        self.stdout.write(self.style.SUCCESS(f"  Créée : {nom_fr}"))

            except Exception as exc:
                skipped += 1
                self.stderr.write(self.style.ERROR(f"  Forme {idx} : erreur {exc}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nImport terminé : {created} créée(s), {updated} mise(s) à jour, {skipped} ignorée(s)."
        ))
