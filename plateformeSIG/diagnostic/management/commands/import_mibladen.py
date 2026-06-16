# -*- coding: utf-8 -*-
"""Import du lot « Perimetre Mibladen finale » (commune Mibladen, province Midelt).

Lit `static/Perimetre Mibladen finale/diagnostic finalee.xlsx` et insère
les périmètres et leurs ouvrages dans l'app diagnostic, en appliquant les
règles de transformation décrites dans PLAN_INSERTION_MIBLADEN.md (notamment
l'inversion d'échelle des notes 0-5, §8.5).

    python manage.py import_mibladen [--reset] [--dry-run]
"""

import os
import unicodedata

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.gis.geos import Point, GEOSGeometry, WKBWriter
from django.contrib.gis.gdal import DataSource

from carte.models import Commune
from diagnostic.models import (
    CULTURES_TAFILALET,
    Perimetre, Assolement, TourEau, OrganisationAgriculteur,
    Seuil, EtatSeuil,
    MurProtection, EtatMurProtection,
    Seguias, TronconSeguia, EtatTronconSeguia,
)

COMMUNE_NOM = "Mibladen"
DOSSIER = "Perimetre Mibladen finale"
FICHIER = "diagnostic finalee.xlsx"

SRID_NORD_MAROC = 26191      # Merchich / Nord Maroc (CRS des shapefiles et des coords X/Y)
SRID_WGS84 = 4326

SHP_PERIMETRE = os.path.join("Perimetre Mibladen finale", "Perimetre Miblanden finale.shp")
SHP_SEGUIAS = os.path.join("saguia Milbaden", "saguia Milbaden", "seguias Milbaden.shp")


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def norm(s):
    """minuscule, sans accents, espaces compactés."""
    if s is None:
        return ""
    s = " ".join(str(s).split())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def to_float(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def to_int(v):
    f = to_float(v)
    return None if f is None else int(round(f))


def f0(v):
    """float avec défaut 0 (champs NOT NULL sans valeur)."""
    f = to_float(v)
    return 0.0 if f is None else f


def pct100(v):
    """Fraction Excel (0–1) → pourcentage (0–100), convention de l'application
    (formulaire « % … / 100 », bilan `pourcentage/100`). None conservé."""
    f = to_float(v)
    return None if f is None else round(f * 100, 4)


def pct100_0(v):
    """Comme pct100 mais 0 par défaut (champs NOT NULL : parcelles_*)."""
    f = to_float(v)
    return 0.0 if f is None else round(f * 100, 4)


def txt(v):
    return "" if v is None else " ".join(str(v).split())


def inv_note(v):
    """Règle 1 §8.5 : inversion d'échelle. 0 reste 0, sinon 5 - v."""
    n = to_int(v)
    if n is None:
        return None
    if n == 0:
        return 0
    n = max(0, min(5, n))
    return 5 - n


def type_de_sol(v):
    n = norm(v)
    if "limon" in n:
        return "limoneux"
    if "argil" in n:
        return "argileux"
    if "sabl" in n:
        return "sableux"
    if "caillou" in n:
        return "caillouteux"
    return "mixte"


def niveau_fertilite(v):
    n = norm(v)
    if "bon" in n:
        return "bon"
    if "moyen" in n:
        return "moyen"
    if "faible" in n:
        return "faible"
    return "bon"


def etat_general_diag(v):
    """Texte Excel → ETAT_CONSTRUCTION_DIAG_CHOICES (§8.1)."""
    n = norm(v)
    if not n:
        return ""
    if "detruit" in n:                       # inclut « Mauvais à détruit »
        return "t_mauvais"
    if "moyen" in n and "mauvais" in n:
        return "moyen_mauvais"
    if "moyen" in n and "bon" in n:
        return "moyen_bon"
    if "mauvais" in n:
        return "mauvais"
    if "moyen" in n:
        return "moyen"
    if "bon" in n:
        return "bon"
    return ""


def etat_materiel(v):
    """Texte Excel → ETAT_MATERIEL_HYDROMECA_CHOICES."""
    n = norm(v)
    if not n:
        return ""
    if "absen" in n:
        return "absence"
    if "tres mauvais" in n:
        return "t_mauvais"
    if "moyen" in n and "mauvais" in n:
        return "moyen_mauvais"
    if "moyen" in n and "bon" in n:
        return "moyen_bon"
    if "mauvais" in n:
        return "mauvais"
    if "moyen" in n:
        return "moyen"
    if "bon" in n:
        return "bon"
    return ""


CULTURE_MAP = {
    "peche": "Peche", "olivier": "Olive", "olive": "Olive",
    "ble dur": "Blé", "ble": "Blé", "mais": "Mais",
    "abricot": "Abricot", "luzerne": "Luzerne",
}
_VALID_CULTURES = {c for c, _ in CULTURES_TAFILALET}


def map_culture(v):
    n = norm(v)
    return CULTURE_MAP.get(n)


def unite_rendement(v):
    n = norm(v)
    if "kg" in n and "arbre" in n:
        return "kg_arbre"
    return "qx_ha"   # « q/ha » et « q » seuls


def type_seguia(v):
    n = norm(v)
    if "princ" in n:
        return "principale"
    if "second" in n:
        return "secondaire"
    if "terti" in n:
        return "tertiaire"
    return "principale"


def nature_seguia(v):
    n = norm(v)
    if "arme" in n:
        return "beton_arme"
    if "beton" in n:
        return "beton"
    if "terre" in n:
        return "terre"
    return "autre"   # maçonnerie, etc.


def type_ecoulement(v):
    n = norm(v)
    if "dalot" in n:
        return "dalot"
    return "ciel_ouvert"


def canon_seguia(nom):
    """Nom de séguia canonique pour la jointure shp ↔ DB :
    minuscule sans accents, contenu des parenthèses retiré (« (tranch 1) »,
    « (secondaire) »…), « charfa » réduit à « saguia charfa »."""
    import re
    n = norm(nom)
    n = re.sub(r"\(.*?\)", "", n).strip()
    n = " ".join(n.split())
    if "charfa" in n:
        return "saguia charfa"
    return n


def rows(ws, start):
    """Lignes de données (>= index `start`) non vides."""
    data = list(ws.iter_rows(values_only=True))[start:]
    return [r for r in data if r and any(c is not None and str(c).strip() for c in r)]


# ──────────────────────────────────────────────────────────────────────────
# Commande
# ──────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Importe le lot des périmètres de Mibladen depuis diagnostic finalee.xlsx"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Supprime d'abord les périmètres existants de la commune Mibladen.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Effectue l'import dans une transaction annulée (aucune écriture persistée).")

    def handle(self, *args, **opts):
        import openpyxl

        path = self._find_xlsx()
        self.stdout.write(f"Fichier : {path}")

        try:
            commune = Commune.objects.get(nom_fr=COMMUNE_NOM)
        except Commune.DoesNotExist:
            raise CommandError(f"Commune '{COMMUNE_NOM}' introuvable dans carte.Commune.")

        dossier = os.path.dirname(path)
        wb = openpyxl.load_workbook(path, data_only=True)
        self._perim_geoms = self._load_perimetre_geoms(dossier)
        self._seguia_geoms = self._load_seguia_geoms(dossier)

        existing = Perimetre.objects.filter(commune_territoriale__iexact=COMMUNE_NOM)
        if existing.exists() and not opts["reset"]:
            raise CommandError(
                f"{existing.count()} périmètre(s) Mibladen déjà présents. "
                "Relancez avec --reset pour les remplacer."
            )

        try:
            with transaction.atomic():
                if opts["reset"] and existing.exists():
                    n = existing.count()
                    existing.delete()
                    self.stdout.write(self.style.WARNING(f"--reset : {n} périmètre(s) Mibladen supprimés."))

                perim_map = self._import_perimetres(wb, commune)
                self._import_seuils(wb, perim_map)
                self._import_murs(wb, perim_map)
                self._import_seguias(wb, perim_map)
                self._import_assolement(wb, perim_map)
                self._import_tours_eau(wb, perim_map)
                self._import_organisations(wb, perim_map)

                self._recap()

                if opts["dry_run"]:
                    raise _DryRun()
        except _DryRun:
            self.stdout.write(self.style.WARNING("--dry-run : transaction annulée, rien n'a été persisté."))
            return

        self.stdout.write(self.style.SUCCESS("Import terminé."))

    # ── localisation du fichier ────────────────────────────────────────────
    def _find_xlsx(self):
        candidates = []
        for d in getattr(settings, "STATICFILES_DIRS", []):
            candidates.append(os.path.join(str(d), DOSSIER, FICHIER))
        candidates.append(os.path.join(str(settings.BASE_DIR), "plateformeSIG", "static", DOSSIER, FICHIER))
        for c in candidates:
            if os.path.exists(c):
                return c
        raise CommandError(f"Fichier introuvable. Cherché : {candidates}")

    # ── chargement des géométries (shapefiles, reprojetées en 4326) ─────────
    @staticmethod
    def _ogr_to_geos(feat):
        g = feat.geom
        g.transform(SRID_WGS84)
        geos = GEOSGeometry(g.wkt, srid=SRID_WGS84)
        if geos.hasz:                       # aplatit la 3D (Polygon25D → Polygon)
            w = WKBWriter()
            w.outdim = 2
            geos = GEOSGeometry(w.write_hex(geos), srid=SRID_WGS84)
        return geos

    def _load_perimetre_geoms(self, dossier):
        """{nom_de_per normalisé : Polygon 4326}."""
        path = os.path.join(dossier, SHP_PERIMETRE)
        out = {}
        if not os.path.exists(path):
            self.stderr.write(f"  ! Shapefile périmètre introuvable : {path}")
            return out
        lyr = DataSource(path)[0]
        for feat in lyr:
            out[norm(feat.get("nom_de_per"))] = self._ogr_to_geos(feat)
        return out

    def _load_seguia_geoms(self, dossier):
        """{(périmètre normalisé, nom canonique séguia) : [LineString 4326 ordonnées]}."""
        path = os.path.join(dossier, SHP_SEGUIAS)
        groups = {}
        if not os.path.exists(path):
            self.stderr.write(f"  ! Shapefile séguias introuvable : {path}")
            return groups
        lyr = DataSource(path)[0]
        feats = []
        for feat in lyr:
            try:
                num = int(feat.get("Numéro"))
            except (TypeError, ValueError):
                num = 0
            feats.append((num, feat))
        feats.sort(key=lambda x: x[0])
        for _, feat in feats:
            per = norm(feat.get("nom_de_per"))
            nom = canon_seguia(feat.get("Nom_ségui"))
            groups.setdefault((per, nom), []).append(self._ogr_to_geos(feat))
        return groups

    # ── Périmètres ──────────────────────────────────────────────────────────
    def _import_perimetres(self, wb, commune):
        ws = wb["Perimetre"]
        perim_map = {}
        for r in rows(ws, 1):
            nom = txt(r[1])
            if not nom:
                continue
            p = Perimetre.objects.create(
                province="Midelt",
                coordination="Midelt",
                commune_territoriale=COMMUNE_NOM,
                commune=commune,
                ksar_village=txt(r[7]),
                temperature_moyenne_annuelle=to_float(r[8]),
                precipitations_moyennes_annuelles=to_float(r[9]),
                vent=txt(r[10]) or None,
                humidite=txt(r[11]) or None,
                nombre_beneficiaires=to_int(r[12]) or 0,
                nombre_menages=to_int(r[13]) or 0,
                superficie_totale=f0(r[14]),
                superficie_agricole_utile=f0(r[15]),
                superficie_irriguee=f0(r[16]),
                superficie_en_bour=f0(r[17]),
                type_de_sol=type_de_sol(r[18]),
                niveau_de_fertilite=niveau_fertilite(r[19]),
                parcelles_moins_1ha=pct100_0(r[20]),
                parcelles_1_a_3ha=pct100_0(r[21]),
                parcelles_plus_3ha=pct100_0(r[22]),
                statut_juridique_melk=pct100(r[23]),
                statut_juridique_collectif=pct100(r[24]),
                statut_juridique_location=pct100(r[25]),
                statut_juridique_guiche=pct100(r[26]),
                statut_juridique_habousse=pct100(r[27]),
                moyenne_bovins=to_float(r[28]),
                moyenne_ovins=to_float(r[29]),
                moyenne_caprins=to_float(r[30]),
                geometrie=self._perim_geoms.get(norm(nom)),
                statut="valide",
            )
            perim_map[norm(nom)] = p
        nb_geom = sum(1 for p in perim_map.values() if p.geometrie is not None)
        self.stdout.write(f"  Périmètres : {len(perim_map)} (géométrie : {nb_geom})")
        return perim_map

    def _perim(self, perim_map, nom):
        return perim_map.get(norm(nom))

    # ── Seuils + EtatSeuil ──────────────────────────────────────────────────
    def _import_seuils(self, wb, perim_map):
        ws = wb["Seuil"]
        n = 0
        for r in rows(ws, 1):
            p = self._perim(perim_map, r[4])
            if p is None:
                self.stderr.write(f"  ! Seuil '{txt(r[1])}' : périmètre '{txt(r[4])}' introuvable, ignoré.")
                continue
            etat_txt = txt(r[26])
            cx, cy = to_float(r[2]), to_float(r[3])
            geom = None
            if cx is not None and cy is not None:
                geom = Point(cx, cy, srid=SRID_NORD_MAROC)
                geom.transform(SRID_WGS84)
            s = Seuil.objects.create(
                perimetre=p,
                nom_du_seuil=txt(r[1]),
                coordonnes_x=cx,
                coordonnes_y=cy,
                geometrie=geom,
                nature_du_seuil=txt(r[5]),
                type_du_seuil=txt(r[6]),
                materiaux_de_construction=txt(r[7]),
                debit_mobilise=f0(r[8]),
                longueur=f0(r[9]),
                largeur_de_base=f0(r[10]),
                hauteur=f0(r[11]),
                largeur_tapis_amortissement=f0(r[12]),
                longueur_prise_droit=to_float(r[13]),
                largeur_prise_droit=to_float(r[14]),
                nbr_pertuis_prise_droit=to_float(r[15]),
                longueur_prise_gauche=to_float(r[16]),
                largeur_prise_gauche=to_float(r[17]),
                nbr_pertuis_prise_gauche=to_float(r[18]),
                longueur_degrevement_droit=to_float(r[19]),
                largeur_degrevement_droit=to_float(r[20]),
                nbr_pertuis_degrevement_droit=to_float(r[21]),
                longueur_degrevement_gauche=to_float(r[22]),
                largeur_degrevement_gauche=to_float(r[23]),
                nbr_pertuis_degrevement_gauche=to_float(r[24]),
                etat_construction_fonctionnement=etat_txt,
                etat_materiel_hydromecanique=txt(r[27]),
                annee_derniere_rehabilitation=to_int(r[28]),
                statut="valide",
            )
            # 10 notes (cols 29..38) avec inversion §8.5
            notes = {
                "etat_structurel_digue": inv_note(r[29]),
                "affouillement_aval":    inv_note(r[30]),
                "etat_vannes":           inv_note(r[31]),
                "infiltration_fuite":    inv_note(r[32]),
                "murs_guideaux":         inv_note(r[33]),
                "radier_aval":           inv_note(r[34]),
                "degradation_beton":     inv_note(r[35]),
                "limiteur_debit":        inv_note(r[36]),
                "envasement_retenue":    inv_note(r[37]),
                "dessableur":            inv_note(r[38]),
            }
            notes = self._apply_destruction_rules(etat_txt, notes,
                                                   champs_crue=("etat_structurel_digue",
                                                                "degradation_beton",
                                                                "infiltration_fuite"))
            EtatSeuil.objects.create(
                seuil=s,
                etat_construction_fonctionnement=etat_general_diag(etat_txt),
                etat_materiel_hydromecanique=etat_materiel(r[27]),
                **notes,
            )
            n += 1
        self.stdout.write(f"  Seuils : {n}")

    def _apply_destruction_rules(self, etat_txt, notes, champs_crue):
        """Règles 2 & 3 §8.5."""
        ne = norm(etat_txt)
        if "detruit" in ne and "complet" in ne:          # Règle 2
            return {k: 5 for k in notes}
        if "detruit" in ne and "crue" in ne:             # Règle 3
            for k in champs_crue:
                if k in notes:
                    notes[k] = 5
        return notes

    # ── Murs de protection + EtatMurProtection ──────────────────────────────
    def _import_murs(self, wb, perim_map):
        ws = wb["Murs de protection\xa0"]
        n = 0
        for r in rows(ws, 2):
            p = self._perim(perim_map, r[2])
            if p is None:
                self.stderr.write(f"  ! Mur '{txt(r[1])}' : périmètre '{txt(r[2])}' introuvable, ignoré.")
                continue
            rive = "droite" if "droit" in norm(r[3]) else "gauche"
            position = "amont" if "amont" in norm(r[4]) else "aval"
            etat_txt = txt(r[10])
            m = MurProtection.objects.create(
                perimetre=p,
                nom_mur_protection=txt(r[1]) or None,
                rive=rive,
                position=position,
                nature_materiaux=txt(r[5]),
                longueur=f0(r[6]),
                hauteur=f0(r[7]),
                epaisseur_superieure=f0(r[8]),
                epaisseur_inferieure=f0(r[9]),
                etat_construction=etat_txt,
                statut="valide",
            )
            # Mur « Détruit » → notes = 5 (esprit règle 2, point #15)
            note = 5 if "detruit" in norm(etat_txt) else None
            EtatMurProtection.objects.create(
                mur=m,
                etat_general=etat_general_diag(etat_txt),
                valide=True,
                fissures_revetement=note,
                degradation_beton=note,
                risque_contournement=note,
            )
            n += 1
        self.stdout.write(f"  Murs de protection : {n}")

    # ── Séguias + Tronçons + EtatTronconSeguia ──────────────────────────────
    def _import_seguias(self, wb, perim_map):
        ws = wb["Seguias"]
        pk2norm = {p.pk: k for k, p in perim_map.items()}
        # Regroupement par (périmètre, nom canonique, type)
        groupes = {}
        ordre_cle = []
        for r in rows(ws, 1):
            p = self._perim(perim_map, r[1])
            if p is None:
                self.stderr.write(f"  ! Séguia '{txt(r[2])}' : périmètre '{txt(r[1])}' introuvable, ignorée.")
                continue
            nom = txt(r[2])
            if "charfa" in norm(nom):          # consolidation §7-1
                nom = "Saguia Charfa"
            typ = type_seguia(r[4])
            cle = (p.pk, nom, typ)
            if cle not in groupes:
                groupes[cle] = {"perimetre": p, "nom": nom, "type": typ, "lignes": []}
                ordre_cle.append(cle)
            groupes[cle]["lignes"].append(r)

        # Pour distinguer les séguias de même (périmètre, nom) mais de type différent
        # (cas Ait Hourir RD/RG secondaire+tertiaire, §7-2) → suffixe du type.
        from collections import Counter
        compte_nom = Counter((g["perimetre"].pk, g["nom"]) for g in groupes.values())

        nb_seg = nb_tr = nb_tr_geom = 0
        for cle in ordre_cle:
            g = groupes[cle]
            nom_final = g["nom"]
            if compte_nom[(g["perimetre"].pk, g["nom"])] > 1:
                nom_final = f"{g['nom']} ({g['type']})"
            seg = Seguias.objects.create(
                perimetre=g["perimetre"],
                nom_de_la_seguia=nom_final,
                type_deguia=g["type"],
            )
            nb_seg += 1
            geom_key = (pk2norm.get(g["perimetre"].pk), canon_seguia(g["nom"]))
            geom_queue = self._seguia_geoms.get(geom_key)
            vus = set()
            for r in g["lignes"]:
                tr = txt(r[3]).upper().replace(" ", "")
                if tr in vus:
                    self.stderr.write(f"  ! Tronçon dupliqué {tr} sur '{nom_final}', ignoré.")
                    continue
                vus.add(tr)
                etat_txt = txt(r[14])
                geom = geom_queue.pop(0) if geom_queue else None
                t = TronconSeguia.objects.create(
                    seguia=seg,
                    troncon=tr or "TR1",
                    longueur=f0(r[5]),
                    largeur_meroire=to_float(r[6]),
                    hauteur=to_float(r[7]),
                    hauteur_eau=f0(r[8]),
                    debit=f0(r[9]) / 1000.0,          # l/s → m³/s
                    fruit_de_berge=to_float(r[10]) or 0,
                    epaisseur_parois=f0(r[11]),
                    nature=nature_seguia(r[12]),
                    type_decoulement=type_ecoulement(r[13]),
                    geometrie=geom,
                    statut="valide",
                )
                if geom is not None:
                    nb_tr_geom += 1
                notes = {
                    "fissures_revetement": inv_note(r[15]),
                    "infiltration_fuite":  inv_note(r[16]),
                    "obstructions_debris": inv_note(r[17]),
                    "erosion_berges":      inv_note(r[18]),
                    "sedimentation_fond":  inv_note(r[19]),
                    "ouvrages_regulation": inv_note(r[20]),
                    "spalling_beton":      inv_note(r[21]),
                }
                notes = self._apply_destruction_rules(
                    etat_txt, notes,
                    champs_crue=("infiltration_fuite", "spalling_beton"))
                EtatTronconSeguia.objects.create(
                    troncon=t,
                    etat_general=etat_general_diag(etat_txt),
                    valide=True,
                    **notes,
                )
                nb_tr += 1
        self.stdout.write(f"  Séguias : {nb_seg} / Tronçons : {nb_tr} (géométrie : {nb_tr_geom})")

    # ── Assolement ──────────────────────────────────────────────────────────
    def _import_assolement(self, wb, perim_map):
        ws = wb["Assolement"]
        compteur = {}
        n = 0
        for r in rows(ws, 2):
            p = self._perim(perim_map, r[0])
            if p is None:
                continue
            culture = map_culture(r[1])
            if culture not in _VALID_CULTURES:
                self.stderr.write(f"  ! Culture '{txt(r[1])}' non reconnue, ligne ignorée.")
                continue
            # La colonne « Surface » de l'Excel est en « pied » (nb d'arbres) pour
            # plusieurs périmètres : le pourcentage fait foi. surface_ha est donc
            # dérivé du pourcentage × superficie agricole utile (cohérent avec les
            # surfaces en ha déjà fournies, ex. Ahouli Abricot 0.3 × 26 = 7.8 ha).
            pct = to_float(r[4])              # fraction Excel (0–1)
            surface_ha = None
            if pct is not None and p.superficie_agricole_utile:
                surface_ha = round(pct * p.superficie_agricole_utile, 2)
            ordre = compteur.get(p.pk, 0)
            compteur[p.pk] = ordre + 1
            Assolement.objects.create(
                perimetre=p,
                culture=culture,
                pourcentage=(round(pct * 100, 4) if pct is not None else None),  # stocké en % (0–100)
                surface_ha=surface_ha,
                rendement=to_float(r[5]),
                unite_rendement=unite_rendement(r[6]),
                ordre=ordre,
            )
            n += 1
        self.stdout.write(f"  Assolement : {n}")

    # ── Tours d'eau ─────────────────────────────────────────────────────────
    def _import_tours_eau(self, wb, perim_map):
        ws = wb["tours_eau"]
        compteur = {}
        n = 0
        for r in rows(ws, 2):
            p = self._perim(perim_map, r[0])
            if p is None:
                continue
            ayant = txt(r[1])
            cycle = to_float(r[2])
            cycle_txt = txt(r[2])
            if cycle is None and cycle_txt:        # ex. « Gravitaire »
                ayant = f"{ayant} — {cycle_txt}".strip(" —")
            ordre = compteur.get(p.pk, 0)
            compteur[p.pk] = ordre + 1
            TourEau.objects.create(
                perimetre=p,
                ayant_droit=ayant,
                cycle_jours=cycle,
                duree_heures=to_float(r[3]),
                ordre=ordre,
            )
            n += 1
        self.stdout.write(f"  Tours d'eau : {n}")

    # ── Organisations ───────────────────────────────────────────────────────
    def _import_organisations(self, wb, perim_map):
        ws = wb["organisations"]
        compteur = {}
        n = 0
        for r in rows(ws, 2):
            p = self._perim(perim_map, r[0])
            if p is None:
                continue
            nom = txt(r[1])
            if not nom:
                continue
            ordre = compteur.get(p.pk, 0)
            compteur[p.pk] = ordre + 1
            OrganisationAgriculteur.objects.create(perimetre=p, nom=nom, ordre=ordre)
            n += 1
        self.stdout.write(f"  Organisations : {n}")

    # ── Récapitulatif ─────────────────────────────────────────────────────--
    def _recap(self):
        per = Perimetre.objects.filter(commune_territoriale__iexact=COMMUNE_NOM)
        self.stdout.write(self.style.HTTP_INFO("── Récapitulatif (commune Mibladen) ──"))
        seuils = Seuil.objects.filter(perimetre__in=per)
        troncons = TronconSeguia.objects.filter(seguia__perimetre__in=per)
        self.stdout.write(f"  Perimetre              : {per.count()} (géom: {per.exclude(geometrie__isnull=True).count()})")
        self.stdout.write(f"  Seuil                  : {seuils.count()} (géom: {seuils.exclude(geometrie__isnull=True).count()})")
        self.stdout.write(f"  MurProtection          : {MurProtection.objects.filter(perimetre__in=per).count()}")
        self.stdout.write(f"  Seguias                : {Seguias.objects.filter(perimetre__in=per).count()}")
        self.stdout.write(f"  TronconSeguia          : {troncons.count()} (géom: {troncons.exclude(geometrie__isnull=True).count()})")
        self.stdout.write(f"  Assolement             : {Assolement.objects.filter(perimetre__in=per).count()}")
        self.stdout.write(f"  TourEau                : {TourEau.objects.filter(perimetre__in=per).count()}")
        self.stdout.write(f"  OrganisationAgriculteur: {OrganisationAgriculteur.objects.filter(perimetre__in=per).count()}")


class _DryRun(Exception):
    """Sentinelle interne pour annuler la transaction en --dry-run."""
    pass
