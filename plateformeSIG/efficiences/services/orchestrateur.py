"""
Orchestrateur du calcul complet pour un ouvrage de tete.

Enchaine les quatre niveaux :
    1. calcul par tronçon avec propagation séquentielle du débit (Pi/Pv inchangés)
    2. efficience par séguia = Q_sortie / Q_entrée  (cascade interne)
    3. agrégation par catégorie (moyenne pondérée par Q_entrée de chaque séguia)
    4. cascade globale P × S × T et persistance dans Efficience

Le tout dans une transaction atomique.
"""

from collections import defaultdict

from django.db import transaction

from diagnostic.models import TronconSeguia, SguiaAssocie_OuvrageTete

from .agregation import (
    compter_troncons_par_categorie,
    efficience_globale_cascade,
    efficience_par_categorie,
)
from .efficience_troncon import calculer_efficience_troncon


# Mapping entre le type d'ouvrage et le champ FK correspondant
# dans SguiaAssocie_OuvrageTete.
OUVRAGE_TETE_FK_MAP = {
    'seuil': 'FK_seuil',
    'prise_locale': 'FK_prise_locale',
    'khettara': 'FK_khettaras',
    'forage_puits': 'FK_puit_forage',
    'barrage_retenue': 'FK_barrage_retenue',
}

OUVRAGE_TETE_LABEL = {
    'seuil': 'Seuil',
    'prise_locale': 'Prise locale',
    'khettara': 'Khettara',
    'forage_puits': 'Forage / Puits',
    'barrage_retenue': 'Barrage de retenue',
}

TYPE_ORDER = {
    'principale': 0,
    'secondaire': 1,
    'tertiaire': 2,
}

OUVRAGE_FIELDS = (
    ('seuil', 'FK_seuil'),
    ('prise_locale', 'FK_prise_locale'),
    ('khettara', 'FK_khettaras'),
    ('forage_puits', 'FK_puit_forage'),
    ('barrage_retenue', 'FK_barrage_retenue'),
)


def _safe_ratio_percent(numerator, denominator):
    if denominator and denominator > 0:
        return (numerator / denominator) * 100
    return None


def _aggregat_depuis_details(details):
    total_debit = sum((d.get('debit_amont') or 0.0) for d in details)
    total_pi = sum((d.get('perte_infiltration_m3s') or 0.0) for d in details)
    total_pv = sum((d.get('perte_vaporisation_m3s') or 0.0) for d in details)
    total_pertes = total_pi + total_pv

    if total_debit > 0:
        eff_moy_pond = sum(
            (d.get('efficience_pourcent') or 0.0) * (d.get('debit_amont') or 0.0)
            for d in details
        ) / total_debit
    elif details:
        eff_moy_pond = sum((d.get('efficience_pourcent') or 0.0) for d in details) / len(details)
    else:
        eff_moy_pond = None

    return {
        'nb_troncons': len(details),
        'debit_total_m3s': total_debit,
        'perte_infiltration_totale_m3s': total_pi,
        'perte_vaporisation_totale_m3s': total_pv,
        'perte_totale_m3s': total_pertes,
        'efficience_moyenne_ponderee': eff_moy_pond,
        'taux_perte_global_pourcent': _safe_ratio_percent(total_pertes, total_debit),
    }


def _tableau_par_type(details_par_troncon):
    buckets = defaultdict(list)
    labels = {}

    for d in details_par_troncon:
        type_code = d.get('type_seguia_code') or 'non_renseigne'
        buckets[type_code].append(d)
        labels[type_code] = d.get('type_seguia_label') or 'Non renseigne'

    lignes = []
    for type_code, items in buckets.items():
        agg = _aggregat_depuis_details(items)
        lignes.append({
            'type_code': type_code,
            'type_label': labels.get(type_code, 'Non renseigne'),
            **agg,
        })

    lignes.sort(key=lambda x: TYPE_ORDER.get(x['type_code'], 99))
    return lignes


def _tableau_par_ouvrage(details_par_troncon, ouvrage_tete_type, ouvrage_tete_id):
    detail_by_parent_id = {d['seguia_parent_id']: d for d in details_par_troncon}
    parent_ids = list(detail_by_parent_id.keys())
    if not parent_ids:
        return []

    liaisons = (
        SguiaAssocie_OuvrageTete.objects
        .filter(FK_nom_sguia_id__in=parent_ids)
        .select_related('FK_seuil', 'FK_prise_locale', 'FK_khettaras', 'FK_puit_forage', 'FK_barrage_retenue')
    )

    buckets = defaultdict(list)
    seen = defaultdict(set)

    for liaison in liaisons:
        detail = detail_by_parent_id.get(liaison.FK_nom_sguia_id)
        if detail is None:
            continue

        for type_code, field_name in OUVRAGE_FIELDS:
            ouvrage = getattr(liaison, field_name, None)
            if ouvrage is None:
                continue
            key = (type_code, ouvrage.id)
            troncon_id = detail['troncon_id']
            if troncon_id in seen[key]:
                continue
            seen[key].add(troncon_id)
            buckets[key].append(detail)

    if not buckets:
        buckets[(ouvrage_tete_type, ouvrage_tete_id)] = details_par_troncon

    lignes = []
    for (type_code, oid), items in buckets.items():
        agg = _aggregat_depuis_details(items)
        lignes.append({
            'ouvrage_tete_type': type_code,
            'ouvrage_tete_id': oid,
            'ouvrage_label': OUVRAGE_TETE_LABEL.get(type_code, type_code),
            'is_selected': (type_code == ouvrage_tete_type and oid == ouvrage_tete_id),
            **agg,
        })

    lignes.sort(key=lambda x: (x['ouvrage_label'], x['ouvrage_tete_id']))
    return lignes


def seguias_liees_a_ouvrage(perimetre, ouvrage_tete_type, ouvrage_tete_id):
    """Récupère les TronconSeguia du périmètre liés à un ouvrage de tête (via séguia parente)."""
    fk_field = OUVRAGE_TETE_FK_MAP[ouvrage_tete_type]
    lookup = f'seguia__ouvrages_tete_associes__{fk_field}_id'
    return (
        TronconSeguia.objects
        .filter(seguia__perimetre=perimetre, **{lookup: ouvrage_tete_id})
        .select_related('seguia')
        .distinct()
    )


@transaction.atomic
def calculer_efficience_complete(perimetre, ouvrage_tete_type, ouvrage_tete_id, operateur=None):
    """Calcule et persiste l'efficience complete d'un ouvrage de tete.

    Retourne un dict {efficience, details_par_troncon, ...}.
    """
    from efficiences.models import Efficience  # import local pour eviter le cycle

    troncons = list(seguias_liees_a_ouvrage(perimetre, ouvrage_tete_type, ouvrage_tete_id))

    # ── Niveau 1 & 2 : grouper par séguia, propager Q, calculer E_seguia ──

    # Regrouper les tronçons par séguia et ordonner TR1 → TR2 → …
    troncons_by_seguia = defaultdict(list)
    for tr in troncons:
        troncons_by_seguia[tr.seguia_id].append(tr)
    for seg_id in troncons_by_seguia:
        troncons_by_seguia[seg_id].sort(key=lambda t: t.troncon)

    details_par_troncon = []  # détails tronçon par tronçon (pour les graphes)
    suivis_seguias = []       # résumé par séguia (pour l'agrégation catégorie)

    for seg_id, seg_troncons in troncons_by_seguia.items():
        seguia = seg_troncons[0].seguia

        # Q_entrée = débit stocké sur le 1er tronçon (TR1)
        q_entree = seg_troncons[0].debit or 0.0
        q_courant = q_entree  # débit propagé de tronçon en tronçon

        for tr in seg_troncons:
            details = calculer_efficience_troncon(
                tr,
                perimetre=tr.seguia.perimetre,
                q_amont=q_courant,
                persister=True,
            )
            q_courant = details['debit_aval']  # propagation au tronçon suivant

            details_par_troncon.append({
                'troncon_id': tr.id,
                'seguia_parent_id': tr.seguia_id,
                'seguia_nom': f"{seguia.nom_de_la_seguia} — {tr.troncon}",
                'troncon_code': tr.troncon,
                'type_seguia_code': seguia.type_deguia or '',
                'type_seguia_label': seguia.get_type_deguia_display() if seguia.type_deguia else 'Non renseigne',
                'nature_code': tr.nature or '',
                'nature_label': tr.get_nature_display() if tr.nature else 'Non renseignee',
                'type_decoulement_label': tr.get_type_decoulement_display() if tr.type_decoulement else '',
                **details,
            })

        # E_séguia = cascade interne : Q_sortie / Q_entrée
        q_sortie = q_courant
        e_seguia = (q_sortie / q_entree * 100) if q_entree > 0 else 0.0
        e_seguia = max(0.0, min(100.0, e_seguia))

        suivis_seguias.append({
            'efficience': e_seguia,
            'q_entree': q_entree,
            'categorie': seguia.type_deguia or '',
        })

    # ── Niveau 3 & 4 : agrégation catégorie + cascade globale ──

    eff_cat    = efficience_par_categorie(suivis_seguias)
    compteurs  = compter_troncons_par_categorie(details_par_troncon)
    eff_globale = efficience_globale_cascade(eff_cat)

    tableau_par_type    = _tableau_par_type(details_par_troncon)
    tableau_par_ouvrage = _tableau_par_ouvrage(
        details_par_troncon,
        ouvrage_tete_type=ouvrage_tete_type,
        ouvrage_tete_id=ouvrage_tete_id,
    )

    resultat = Efficience.objects.create(
        perimetre=perimetre,
        ouvrage_tete_type=ouvrage_tete_type,
        ouvrage_tete_id=ouvrage_tete_id,
        efficience_principale=eff_cat.get('principale'),
        efficience_secondaire=eff_cat.get('secondaire'),
        efficience_tertiaire=eff_cat.get('tertiaire'),
        efficience_globale=eff_globale,
        nb_troncons_principaux=compteurs['principale'],
        nb_troncons_secondaires=compteurs['secondaire'],
        nb_troncons_tertiaires=compteurs['tertiaire'],
        operateur=operateur,
    )

    return {
        'efficience': resultat,
        'details_par_troncon': details_par_troncon,
        'tableau_par_type': tableau_par_type,
        'tableau_par_ouvrage': tableau_par_ouvrage,
        'efficiences_par_categorie': eff_cat,
        'compteurs': compteurs,
        'efficience_globale_pourcent': eff_globale,
    }
