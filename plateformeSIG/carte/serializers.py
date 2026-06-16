"""Sérialisation GeoJSON par couche à partir du LAYER_REGISTRY."""

import json

from django.apps import apps
from django.contrib.gis.geos import GEOSGeometry
from django.core.serializers import serialize


def _get_model(model_path: str):
    app_label, model_name = model_path.split(".")
    return apps.get_model(app_label, model_name)


def layer_to_geojson(layer_key: str, registry: dict, queryset=None) -> dict:
    """Retourne un dict GeoJSON FeatureCollection pour une couche du registry."""
    meta = registry[layer_key]
    model = _get_model(meta["model"])
    geom_field = meta["geom_field"]
    fields = meta.get("fields", [])

    if queryset is None:
        queryset = model.objects.exclude(**{f"{geom_field}__isnull": True})

    features = []
    for obj in queryset:
        geom = getattr(obj, geom_field)
        if geom is None:
            continue
        properties = {"pk": obj.pk}
        for f in fields:
            val = getattr(obj, f, None)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            properties[f] = val
        features.append({
            "type": "Feature",
            "geometry": json.loads(geom.geojson),
            "properties": properties,
        })

    return {"type": "FeatureCollection", "features": features}
