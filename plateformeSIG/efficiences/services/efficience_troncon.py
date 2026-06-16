"""
Niveau 1 de la cascade : efficience d'un tronçon (séguia).

Formule :
    Q_aval = Q_amont - Pi - Pv
    E      = Q_aval / Q_amont  (clampé [0, 100 %])

Q_amont est propagé depuis le tronçon précédent de la même séguia
(voir orchestrateur). Pi et Pv sont calculés avec les formules inchangées.
"""

from django.utils import timezone

from .coefficients import get_coefficient_c
from .infiltration import perte_infiltration
from .vaporisation import perte_vaporisation


def get_classification(troncon):
    """Catégorie hydraulique du tronçon — lue sur la séguia parente (type_deguia)."""
    return (getattr(troncon, 'seguia', None) and troncon.seguia.type_deguia) or ''


def calculer_efficience_troncon(troncon, perimetre=None, q_amont=None, persister=True):
    """Calcule l'efficience d'un TronconSeguia. Retourne un dict détaillé.

    q_amont : débit entrant (m³/s) propagé depuis le tronçon précédent.
              Si None, on utilise troncon.debit (premier tronçon ou usage isolé).
    Si persister=True, met à jour les champs efficience_* sur le tronçon.
    """
    if perimetre is None:
        perimetre = troncon.seguia.perimetre

    C  = get_coefficient_c(perimetre, troncon)
    Pi = perte_infiltration(troncon, C)
    Pv = perte_vaporisation(troncon, perimetre)

    if q_amont is None:
        q_amont = troncon.debit or 0.0

    q_aval = max(0.0, q_amont - Pi - Pv)

    if q_amont <= 0:
        E = 0.0
    else:
        E = (q_aval / q_amont) * 100
        E = max(0.0, min(100.0, E))

    if persister:
        troncon.efficience_calculee = E
        troncon.perte_infiltration_m3s = Pi
        troncon.perte_vaporisation_m3s = Pv
        troncon.date_dernier_calcul = timezone.now()
        troncon.save(update_fields=[
            'efficience_calculee',
            'perte_infiltration_m3s',
            'perte_vaporisation_m3s',
            'date_dernier_calcul',
        ])

    return {
        'coefficient_c': C,
        'perte_infiltration_m3s': Pi,
        'perte_vaporisation_m3s': Pv,
        'perte_totale_m3s': Pi + Pv,
        'debit_amont': q_amont,
        'debit_aval': q_aval,
        'efficience_pourcent': E,
        'classification': get_classification(troncon),
        'is_dalot': (troncon.type_decoulement or '').lower() == 'dalot',
    }
