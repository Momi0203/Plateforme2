"""
Pertes par évaporation à la surface du canal.

Règle métier : pour un tronçon de type "dalot" (canal fermé / busé,
non exposé à l'air libre), la perte par évaporation est forcée à 0.

Formule (canal à ciel ouvert) :

    Pv = (L * P) * (ET0 / 1000 / 86400)

avec L longueur, P périmètre mouillé (proxy de largeur exposée),
ET0 évapotranspiration de référence en mm/jour lue sur le périmètre.
"""

from .infiltration import perimetre_mouille


def perte_vaporisation(seguia, perimetre):
    """Perte par évaporation en m³/s (zéro pour les dalots)."""
    if (seguia.type_decoulement or '').lower() == 'dalot':
        return 0.0
    et0 = perimetre.et0_mm_jour or 0
    if et0 <= 0:
        return 0.0
    L = seguia.longueur or 0
    P = perimetre_mouille(seguia)
    surface_mouillee = L * P
    et0_m_s = et0 / 1000 / 86400
    return surface_mouillee * et0_m_s
