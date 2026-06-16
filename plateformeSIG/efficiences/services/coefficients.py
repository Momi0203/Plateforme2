"""
Coefficients C de la formule de Davis et Wilson.

Le coefficient dépend du revêtement du canal s'il est revêtu ; sinon,
on retombe sur le type de sol du périmètre.

Sources : référentiel hydraulique adapté au contexte Tafilalet / Midelt.
"""

COEFFICIENTS_SOL = {
    'argileux':         0.15,
    'limono_argileux':  0.18,
    'limoneux':         0.23,
    'sablo_limoneux':   0.260,
    'sableux':          0.30,
    'caillouteux':      0.340,
    'mixte':           0.23,
}

COEFFICIENTS_REVETEMENT = {
    'beton':           0.042,
    'beton_arme':      0.02,
    #'Maçonnerie':      0.055
    'argile_compacte': 0.1,
    'asphalte_leger':  0.087, #'beton_degrade'
}

NATURES_REVETUES = set(COEFFICIENTS_REVETEMENT.keys())


def get_coefficient_c(perimetre, seguia):
    """Retourne le coefficient C applicable à un tronçon.

    Règle : si la séguia est revêtue (béton, béton armé, argile
    compactée, asphalte), on prend le coefficient du revêtement.
    Sinon (terre / autre), on prend le coefficient du sol du périmètre.
    """
    nature = (seguia.nature or '').lower()
    if nature in COEFFICIENTS_REVETEMENT:
        return COEFFICIENTS_REVETEMENT[nature]
    type_sol = (perimetre.type_de_sol or 'mixte').lower()
    return COEFFICIENTS_SOL.get(type_sol, 20)
