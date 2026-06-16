"""Outils géospatiaux — wrappeurs GDAL/GeoDjango pour les endpoints /carte/api/outils/."""

import json

from django.apps import apps
from django.contrib.gis.db.models.functions import Distance, Transform
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D

SRID_METRIQUE = 26191  # Nord Maroc (Lambert conforme conique) — pour calculs en mètres


def _get_model_and_geom(registry, layer_key):
    meta = registry[layer_key]
    app_label, model_name = meta["model"].split(".")
    model = apps.get_model(app_label, model_name)
    return model, meta["geom_field"]


def buffer(registry, layer_key, distance_m: float, pks: list | None = None) -> dict:
    """Retourne un GeoJSON avec la géométrie tampon (union) de la sélection."""
    from django.contrib.gis.db.models import Union as GeoUnion

    model, geom_field = _get_model_and_geom(registry, layer_key)
    qs = model.objects.exclude(**{f"{geom_field}__isnull": True})
    if pks:
        qs = qs.filter(pk__in=pks)

    union = qs.aggregate(u=GeoUnion(geom_field))["u"]
    if union is None:
        return {"type": "FeatureCollection", "features": []}

    buffered = union.transform(SRID_METRIQUE, clone=True).buffer(distance_m)
    buffered.transform(4326)
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": json.loads(buffered.json), "properties": {}}],
    }


def intersection(registry, layer_key_a: str, layer_key_b: str, pks_a: list | None = None) -> dict:
    """Retourne les entités de B qui intersectent la sélection de A."""
    import json

    model_a, geom_a = _get_model_and_geom(registry, layer_key_a)
    model_b, geom_b = _get_model_and_geom(registry, layer_key_b)

    from django.contrib.gis.db.models import Union as GeoUnion
    qs_a = model_a.objects.exclude(**{f"{geom_a}__isnull": True})
    if pks_a:
        qs_a = qs_a.filter(pk__in=pks_a)
    union_a = qs_a.aggregate(u=GeoUnion(geom_a))["u"]
    if union_a is None:
        return {"type": "FeatureCollection", "features": []}

    hits = model_b.objects.filter(**{f"{geom_b}__intersects": union_a})
    features = []
    for obj in hits:
        g = getattr(obj, geom_b)
        features.append({"type": "Feature", "geometry": json.loads(g.geojson), "properties": {"pk": obj.pk}})
    return {"type": "FeatureCollection", "features": features}


def union_couches(registry, layer_key: str, pks: list | None = None) -> dict:
    """Retourne l'union géométrique d'une sélection."""
    import json
    from django.contrib.gis.db.models import Union as GeoUnion

    model, geom_field = _get_model_and_geom(registry, layer_key)
    qs = model.objects.exclude(**{f"{geom_field}__isnull": True})
    if pks:
        qs = qs.filter(pk__in=pks)

    result = qs.aggregate(u=GeoUnion(geom_field))["u"]
    if result is None:
        return {"type": "FeatureCollection", "features": []}
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": json.loads(result.geojson), "properties": {}}],
    }


def dissolve(registry, layer_key: str, champ: str) -> dict:
    """Dissolution par champ : retourne une feature par valeur distincte."""
    import json
    from django.contrib.gis.db.models import Union as GeoUnion

    model, geom_field = _get_model_and_geom(registry, layer_key)
    groups = (
        model.objects
        .exclude(**{f"{geom_field}__isnull": True})
        .values(champ)
        .annotate(geom_union=GeoUnion(geom_field))
    )
    features = []
    for row in groups:
        g = row["geom_union"]
        if g:
            features.append({
                "type": "Feature",
                "geometry": json.loads(g.geojson),
                "properties": {champ: row[champ]},
            })
    return {"type": "FeatureCollection", "features": features}


def near(registry, layer_key_a: str, layer_key_b: str, pks_a: list | None = None) -> list[dict]:
    """Retourne la distance minimale (m) entre chaque entité de A et la couche B."""
    from django.contrib.gis.db.models import Union as GeoUnion

    model_a, geom_a = _get_model_and_geom(registry, layer_key_a)
    model_b, geom_b = _get_model_and_geom(registry, layer_key_b)

    qs_a = model_a.objects.exclude(**{f"{geom_a}__isnull": True})
    if pks_a:
        qs_a = qs_a.filter(pk__in=pks_a)
    union_b = model_b.objects.exclude(**{f"{geom_b}__isnull": True}).aggregate(u=GeoUnion(geom_b))["u"]
    if union_b is None:
        return []

    results = []
    for obj in qs_a.annotate(dist=Distance(Transform(geom_a, SRID_METRIQUE), Transform(union_b, SRID_METRIQUE))):
        results.append({"pk": obj.pk, "distance_m": round(obj.dist.m, 2)})
    return results


def stats_par_zone(registry, layer_key_zones: str, layer_key_valeurs: str, champ_valeur: str, agregats: list[str]) -> list[dict]:
    """Statistiques (count/sum/avg/min/max) de champ_valeur pour chaque zone."""
    from django.contrib.gis.db.models import Union as GeoUnion
    from django.db.models import Avg, Count, Max, Min, Sum

    FUNC_MAP = {"count": Count, "sum": Sum, "avg": Avg, "min": Min, "max": Max}

    model_z, geom_z = _get_model_and_geom(registry, layer_key_zones)
    model_v, geom_v = _get_model_and_geom(registry, layer_key_valeurs)

    results = []
    for zone in model_z.objects.exclude(**{f"{geom_z}__isnull": True}):
        zone_geom = getattr(zone, geom_z)
        qs = model_v.objects.filter(**{f"{geom_v}__intersects": zone_geom})
        agg_kwargs = {k: FUNC_MAP[k](champ_valeur) for k in agregats if k in FUNC_MAP}
        row = qs.aggregate(**agg_kwargs)
        row["zone_pk"] = zone.pk
        results.append(row)
    return results


def manning_troncon(troncon, n_override: float | None = None, pente: float = 0.001) -> dict:
    """Calcule le débit Manning-Strickler Q = (1/n)·A·R^(2/3)·S^(1/2) pour un TronconSeguia.

    Ne touche pas la base de données.
    pente (m/m) : pas stockée sur le modèle — fournie par l'appelant (défaut 0.001).
    """
    import math

    N_NATURE = {'beton': 0.013, 'beton_arme': 0.014, 'terre': 0.025}
    N_FALLBACK = 0.020

    n = n_override if n_override is not None else N_NATURE.get(troncon.nature or '', N_FALLBACK)
    forme = (troncon.forme or 'trapezoidale').lower()
    h = troncon.hauteur_eau or 0.0
    z = troncon.fruit_de_berge or 0.0

    if forme == 'circulaire':
        D = troncon.diametre or 0.0
        if D <= 0 or h <= 0 or n <= 0 or pente <= 0:
            Q = 0.0
        else:
            ratio = min(h / D, 1.0)
            theta = 2.0 * math.pi if ratio >= 1.0 else 2.0 * math.acos(1.0 - 2.0 * ratio)
            A = D ** 2 / 8.0 * (theta - math.sin(theta))
            P = D * theta / 2.0
            R = A / P if P > 0 else 0.0
            Q = (1.0 / n) * A * (R ** (2.0 / 3.0)) * math.sqrt(pente) if R > 0 else 0.0
    else:
        largeur_miroir = troncon.largeur_meroire or 0.0
        b = max(largeur_miroir - 2.0 * h * z, 0.0)
        z_eff = z if forme == 'trapezoidale' else 0.0
        A = (b + z_eff * h) * h
        P = b + 2.0 * h * math.sqrt(1.0 + z_eff ** 2)
        if A <= 0 or P <= 0 or n <= 0 or pente <= 0:
            Q = 0.0
        else:
            R = A / P
            Q = (1.0 / n) * A * (R ** (2.0 / 3.0)) * math.sqrt(pente)

    return {
        'pk': troncon.pk,
        'troncon': troncon.troncon,
        'debit_calcule': round(Q, 6),
        'n_utilise': n,
        'forme': forme,
        'pente': pente,
    }


def scoring(
    registry,
    layer_key: str,
    coefficients: dict[str, float],
    pks: list | None = None,
    n_classes: int = 3,
    methode: str = "jenks",
) -> tuple[list[dict], list[float]]:
    """Scoring composite normalisé + classification.

    score = Σ(coeff_i × note_i) / (5 × Σ coeff_i) × 100

    Returns (resultats, breaks) where:
      resultats : [{pk, score, classe}]   (classe=None if no EtatX exists)
      breaks    : class boundary values [min, b1, ..., max]
    """
    meta = registry[layer_key]
    app_label, model_name = meta["model"].split(".")
    model = apps.get_model(app_label, model_name)
    join_etat = meta.get("join_etat", "diagnostic_etat")

    qs = model.objects.all()
    if pks:
        qs = qs.filter(pk__in=pks)
    qs = qs.select_related(join_etat)

    denom = 5.0 * sum(v for v in coefficients.values())

    rows = []
    for obj in qs:
        etat = getattr(obj, join_etat, None)
        if etat is None:
            rows.append({"pk": obj.pk, "score": None, "classe": None})
            continue
        numerator = sum(
            (getattr(etat, champ, None) or 0) * coeff
            for champ, coeff in coefficients.items()
        )
        score = round((numerator / denom * 100) if denom > 0 else 0.0, 2)
        rows.append({"pk": obj.pk, "score": score, "classe": None})

    valid_scores = sorted(r["score"] for r in rows if r["score"] is not None)
    breaks: list[float] = []

    if len(valid_scores) >= 2:
        k = min(n_classes, len(set(valid_scores)))
        if methode == "quantile":
            breaks = _quantile_breaks(valid_scores, k)
        else:
            breaks = _jenks_breaks(valid_scores, k)

        for r in rows:
            if r["score"] is not None:
                r["classe"] = _assign_class(r["score"], breaks)

    return rows, breaks


# ── Classification helpers ────────────────────────────────────────────────────

def _assign_class(score: float, breaks: list[float]) -> int:
    """1-indexed class from sorted break list [min, b1, ..., max]."""
    for i in range(1, len(breaks)):
        if score <= breaks[i]:
            return i
    return len(breaks) - 1


def _quantile_breaks(data_sorted: list[float], k: int) -> list[float]:
    n = len(data_sorted)
    breaks = [data_sorted[0]]
    for i in range(1, k):
        idx = int(n * i / k)
        breaks.append(data_sorted[max(idx, 0)])
    breaks.append(data_sorted[-1])
    return breaks


def _jenks_breaks(data_sorted: list[float], k: int) -> list[float]:
    """Fisher-Jenks natural breaks: minimise within-class sum of squared deviations."""
    n = len(data_sorted)
    if n == 0:
        return []
    k = min(k, len(set(data_sorted)))
    if k <= 1:
        return [data_sorted[0], data_sorted[-1]]

    # Prefix sums for O(1) SSQ of any sub-range
    S:  list[float] = [0.0] * (n + 1)
    S2: list[float] = [0.0] * (n + 1)
    for i, x in enumerate(data_sorted):
        S[i + 1]  = S[i]  + x
        S2[i + 1] = S2[i] + x * x

    def ssq(lo: int, hi_excl: int) -> float:
        """Sum of squared deviations for data_sorted[lo:hi_excl]."""
        cnt = hi_excl - lo
        if cnt <= 0:
            return 0.0
        s = S[hi_excl] - S[lo]
        return S2[hi_excl] - S2[lo] - s * s / cnt

    INF = float("inf")
    # dp[i][j] = min total SSQ for first i values in j classes
    dp    = [[INF] * (k + 1) for _ in range(n + 1)]
    lower = [[0]   * (k + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0

    for j in range(1, k + 1):
        for i in range(j, n + 1):
            best = INF
            for m in range(j - 1, i):
                cost = dp[m][j - 1] + ssq(m, i)
                if cost < best:
                    best = cost
                    lower[i][j] = m
            dp[i][j] = best

    # Backtrack to recover class start indices
    starts: list[int] = []
    cur = n
    for j in range(k, 0, -1):
        m = lower[cur][j]
        starts.append(m)
        cur = m
    starts.reverse()  # starts[j] = first index of class j+1

    # Build breaks: [data[starts[0]], data[starts[1]], ..., data[-1]]
    breaks = [data_sorted[s] for s in starts]
    breaks.append(data_sorted[-1])
    # Deduplicate while preserving order (edge case: identical values)
    seen: set = set()
    deduped: list[float] = []
    for v in breaks:
        if v not in seen:
            deduped.append(v)
            seen.add(v)
    return deduped
