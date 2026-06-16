"""
Algorithme CPM (Critical Path Method) pour le module Plan d'Action.

Entrée  : queryset TacheIntervention d'un CalendrierIntervention
Sortie  : dict {tache_id: {ES, EF, LS, LF, marge, is_critical}}

Étape 1 — Tri topologique (Kahn)
Étape 2 — Forward pass  : ES = max(EF prédécesseurs), EF = ES + durée
Étape 3 — Backward pass : LF = min(LS successeurs), LS = LF − durée
Étape 4 — Marge totale  = LS − ES ; chemin critique = marge == 0
"""
from collections import defaultdict, deque


def has_cycle(edges, node_ids):
    """
    Retourne True si les arêtes forment un cycle parmi les nœuds actifs.
    edges    : liste de (prédécesseur, successeur) — les deux doivent être dans node_ids
    node_ids : ensemble (set ou itérable) des identifiants de nœuds actifs
    """
    nodes = set(node_ids)
    succ = defaultdict(list)
    in_deg = {n: 0 for n in nodes}

    for pred, suc in edges:
        if pred in nodes and suc in nodes:
            succ[pred].append(suc)
            in_deg[suc] += 1

    queue = deque(n for n, d in in_deg.items() if d == 0)
    visited = 0
    while queue:
        n = queue.popleft()
        visited += 1
        for s in succ[n]:
            in_deg[s] -= 1
            if in_deg[s] == 0:
                queue.append(s)

    return visited != len(nodes)


def compute_cpm(taches_qs):
    """
    Calcule ES/EF/LS/LF et la marge totale pour chaque tâche.

    :param taches_qs: QuerySet<TacheIntervention> d'un calendrier
    :raises ValueError: si un cycle est détecté dans les dépendances
    :returns: dict {tache_id: {ES, EF, LS, LF, marge, is_critical}}
    """
    taches = list(taches_qs.prefetch_related('taches_anterieures'))
    if not taches:
        return {}

    id_to_tache = {t.id: t for t in taches}
    durees = {t.id: t.duree_prevue for t in taches}

    # Graphe de dépendances : successeurs et prédécesseurs
    successeurs = defaultdict(list)
    predecesseurs = defaultdict(list)
    in_degree = {t.id: 0 for t in taches}

    for t in taches:
        for ant in t.taches_anterieures.all():
            if ant.id in id_to_tache:
                successeurs[ant.id].append(t.id)
                predecesseurs[t.id].append(ant.id)
                in_degree[t.id] += 1

    # Étape 1 — Tri topologique de Kahn
    queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
    topo_order = []
    temp_degree = dict(in_degree)

    while queue:
        tid = queue.popleft()
        topo_order.append(tid)
        for succ in successeurs[tid]:
            temp_degree[succ] -= 1
            if temp_degree[succ] == 0:
                queue.append(succ)

    if len(topo_order) != len(taches):
        raise ValueError("Dépendance cyclique détectée dans le calendrier.")

    # Étape 2 — Forward pass
    ES = {tid: 0 for tid in id_to_tache}
    EF = {}
    for tid in topo_order:
        if predecesseurs[tid]:
            ES[tid] = max(EF[p] for p in predecesseurs[tid])
        EF[tid] = ES[tid] + durees[tid]

    # Étape 3 — Backward pass
    project_duration = max(EF.values())
    LF = {tid: project_duration for tid in id_to_tache}
    LS = {}
    for tid in reversed(topo_order):
        if successeurs[tid]:
            LF[tid] = min(LS[s] for s in successeurs[tid])
        LS[tid] = LF[tid] - durees[tid]

    # Étape 4 — Marge + chemin critique
    result = {}
    for tid in id_to_tache:
        marge = LS[tid] - ES[tid]
        result[tid] = {
            'ES': ES[tid],
            'EF': EF[tid],
            'LS': LS[tid],
            'LF': LF[tid],
            'marge': marge,
            'is_critical': marge == 0,
        }

    return result
