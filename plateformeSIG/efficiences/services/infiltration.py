"""
Pertes par infiltration selon la formule de Davis et Wilson.

    Q_perte = 0.45 * C * (h * P * L) / (4_000_000 + 3650 * V * h)

avec h hauteur d'eau, P périmètre mouillé, L longueur, V vitesse
d'écoulement (Q_amont / S).

Les géométries supportées sont trapézoïdale, rectangulaire et
circulaire (pleine section). Pour trapézoïdal/rectangulaire, le
champ `largeur_meroire` représente la largeur au miroir ; la
largeur du fond est déduite via b = largeur_meroire - 2·h·z.
"""

import math


def _largeur_fond(seguia): # il y aune errrur il faut adpter sur la forme trapezuidal et ajouter les autre cas
    """Largeur du fond b (m), déduite de la largeur au miroir."""
    h = seguia.hauteur_eau or 0
    z = seguia.fruit_de_berge or 0
    largeur_miroir = seguia.largeur_meroire or 0
    return max(largeur_miroir - 2 * h * z, 0)


def perimetre_mouille(seguia):
    """Périmètre mouillé P (m) selon la forme du tronçon."""
    forme = (seguia.forme or 'trapezoidale').lower()
    h = seguia.hauteur_eau or 0
    if forme == 'circulaire':
        D = seguia.diametre or 0
        return math.pi * D
    z = seguia.fruit_de_berge or 0
    b = _largeur_fond(seguia)
    return b + 2 * h * math.sqrt(1 + z * z)


def section_mouillee(seguia):
    """Section mouillée S (m²) selon la forme."""
    forme = (seguia.forme or 'trapezoidale').lower()
    h = seguia.hauteur_eau or 0
    if forme == 'circulaire':
        D = seguia.diametre or 0
        return math.pi * D * D / 4
    z = seguia.fruit_de_berge or 0
    b = _largeur_fond(seguia)
    return b * h + z * h * h


def calculer_vitesse(seguia):
    """Vitesse moyenne d'écoulement V (m/s) = Q / S."""
    S = section_mouillee(seguia)
    if S <= 0:
        return 0.0
    return (seguia.debit or 0) / S


def perte_infiltration(seguia, coefficient_c):
    """Perte par infiltration en m³/s."""
    h = seguia.hauteur_eau or 0
    L = seguia.longueur or 0
    S = section_mouillee(seguia)
    P = perimetre_mouille(seguia)
    V = calculer_vitesse(seguia)
    R=S/P  
    return  coefficient_c *((R**0.5) * P )*(L/ 1000)
