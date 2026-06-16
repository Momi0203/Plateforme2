"""
Niveaux 2 et 3 de la cascade :

- Niveau 2 : efficience par catégorie (P/S/T) via moyenne pondérée par le
  débit d'entrée de chaque séguia (Q_entrée = débit du 1er tronçon).
  → chaque séguia compte pour UN point, indépendamment de son nb de tronçons.

- Niveau 3 : efficience globale via produit en cascade.
  Une catégorie sans séguia est neutralisée (facteur = 1).
"""

CATEGORIES = ('principale', 'secondaire', 'tertiaire')


def efficience_par_categorie(suivis_seguias):
    """Moyenne pondérée par Q_entrée pour chaque catégorie présente.

    suivis_seguias : liste de dicts produits par l'orchestrateur, chacun :
        {
          'efficience': float,   # E_seguia en %  (cascade interne tronçons)
          'q_entree':   float,   # débit d'entrée de la séguia (TR1.debit)
          'categorie':  str,     # 'principale' | 'secondaire' | 'tertiaire'
        }

    Retourne {categorie: efficience_pourcent_ou_None}.
    """
    buckets = {cat: [] for cat in CATEGORIES}
    for s in suivis_seguias:
        cat = s.get('categorie', '')
        if cat not in buckets:
            continue
        buckets[cat].append((s['efficience'], s['q_entree']))

    resultats = {}
    for cat, items in buckets.items():
        if not items:
            resultats[cat] = None
            continue
        total_poids = sum(q for _, q in items)
        if total_poids <= 0:
            resultats[cat] = sum(e for e, _ in items) / len(items)
        else:
            resultats[cat] = sum(e * q for e, q in items) / total_poids
    return resultats


def efficience_globale_cascade(efficiences_par_cat):
    """Produit en cascade P × S × T (en %).

    Une catégorie absente (None) → facteur 1.0 (neutralisée).
    """
    facteur = 1.0
    for cat in CATEGORIES:
        e = efficiences_par_cat.get(cat)
        if e is None:
            continue
        facteur *= e / 100
    return facteur * 100


def compter_troncons_par_categorie(details_par_troncon):
    """Compte les tronçons par catégorie depuis les détails de calcul.

    details_par_troncon : liste de dicts avec clé 'type_seguia_code'.
    """
    compteurs = {cat: 0 for cat in CATEGORIES}
    for d in details_par_troncon:
        cat = d.get('type_seguia_code', '')
        if cat in compteurs:
            compteurs[cat] += 1
    return compteurs
