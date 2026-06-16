"""
Pont entre les modèles Django et les fonctions de hydrologie_bv.py.
Toutes les fonctions de calcul proviennent de hydrologie_bv.py (static/).
"""
import math
import sys
from typing import Dict, List, Optional
from django.conf import settings

_hydro_path = str(settings.STATICFILES_DIRS[0])
if _hydro_path not in sys.path:
    sys.path.insert(0, _hydro_path)

from hydrologie_bv import (
    BassinVersant      as HydroBV,
    StationPluviometrique as HydroSP,
    StationHydrometrique  as HydroSH,
    calculer_tc_bv,
    intensites_montana,
    debits_rationnels,
    debits_macmath,
    debits_fuller2,
    debits_mallet_gauthier,
    debits_hazen_lazervic,
    debits_francou_rodier,
    estimer_q10_gradex,
    methode_gradex,
    resultats_finaux,
)

MOIS_SEP_AOU = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aout']
JOURS_MOIS_STD = [30, 31, 30, 31, 31, 28, 31, 30, 31, 30, 31, 31]

PERIODES = [10, 20, 50, 100]

FORMULES_TC_DISPONIBLES = [
    'Kirpich', 'Turraza', 'Bransby', 'Van Te Chow',
    'US Corps', 'Californienne', 'Espagnole', 'Ventura',
]

# Ordre fixe utilisé pour l'affichage et la sérialisation
FORMULES_Q_DISPONIBLES = [
    'Rationnelle', 'Mac-Math', 'Fuller II',
    'Mallet-Gauthier', 'Hazen-Lazervic', 'Francou-Rodier', 'Gradex',
]


# =============================================================================
# Adaptateurs  DB → objets Python de calcul
# =============================================================================

def bv_to_hydro(bv):
    """BassinVersant (Django) → HydroBV (calcul)"""
    return HydroBV(
        nom=bv.nom,
        x_exutoire=bv.x_exutoire,
        y_exutoire=bv.y_exutoire,
        superficie=bv.surface,
        perimetre=bv.perimetre,
        zmin=bv.z_min,
        zmax=bv.z_max,
        z95=None,
        z5=None,
        longueur=bv.thalweg,
    )


def sp_to_hydro(sp):
    """StationPluviometrique (Django) → HydroSP (calcul)"""
    pj24h = {
        T: v for T, v in {
            10: sp.pjmax_t10,  20: sp.pjmax_t20,
            50: sp.pjmax_t50, 100: sp.pjmax_t100,
        }.items() if v is not None
    }
    return HydroSP(
        nom=sp.nom,
        x=sp.x, y=sp.y,
        annees=sp.annees or [],
        pluie=sp.pjmax  or [],
        pj24h=pj24h,
        gradex=sp.grad_exp_pluie,
        hauteur_annuelle=sp.hauteur_moyenne,
    )


def sh_to_hydro(sh):
    """StationHydrometrique (Django) → HydroSH (calcul)"""
    qj = {
        T: v for T, v in {
            10: sh.qjmax_t10,  20: sh.qjmax_t20,
            50: sh.qjmax_t50, 100: sh.qjmax_t100,
        }.items() if v is not None
    }
    return HydroSH(
        nom=sh.nom,
        x=sh.x, y=sh.y,
        annees=sh.annees or [],
        debit=sh.qjmax  or [],
        superficie_jaugee=sh.superficie_bv_jaugee or 0.0,
        qj=qj,
    )


# =============================================================================
# Calcul hydrologique complet
# =============================================================================

def run_analyse(bv_model, sp_model, sh_model, params):
    """
    Lance le calcul hydrologique complet pour un bassin versant.

    Paramètres
    ----------
    bv_model  : instance BassinVersant (Django)
    sp_model  : instance StationPluviometrique (Django)
    sh_model  : instance StationHydrometrique (Django) ou None
    params    : dict nettoyé issu de AnalyseParametresForm

    Retourne un dict sérialisable (JSON-safe) avec tous les résultats.
    """
    bv_obj = bv_to_hydro(bv_model)
    sp_obj = sp_to_hydro(sp_model)
    sh_obj = sh_to_hydro(sh_model) if sh_model else None

    # Coefficients Montana depuis la DB
    montana  = sp_model.coefficients_montana
    a_list = [montana.a10, montana.a20, montana.a50, montana.a100]
    b_list = [montana.b10, montana.b20, montana.b50, montana.b100]

    formules_tc       = params.get('formules_tc') or FORMULES_TC_DISPONIBLES
    formules_q_incluses = params['formules_q_incluses']

    # ── (A) Temps de concentration ──────────────────────────────────────
    tc = calculer_tc_bv(bv_obj, formules_tc, verbose=False)
    Tc_min = tc['Moyenne']
    Tc_h   = Tc_min / 60.0

    # ── (B) Intensités Montana ───────────────────────────────────────────
    intensites = intensites_montana(a_list, b_list, Tc_min, PERIODES)

    # ── (C) Pj24h ────────────────────────────────────────────────────────
    pj24h = {
        T: v for T, v in {
            10: sp_model.pjmax_t10,  20: sp_model.pjmax_t20,
            50: sp_model.pjmax_t50, 100: sp_model.pjmax_t100,
        }.items() if v is not None
    }

    pente = bv_obj.pente()

    # ── (D) Débits par formule ───────────────────────────────────────────
    # Ne calculer que les formules sélectionnées par l'utilisateur
    debits = {}
    if 'Rationnelle' in formules_q_incluses:
        debits['Rationnelle'] = debits_rationnels(
            params['C_rationnel'], intensites, bv_model.surface
        )
    if 'Mac-Math' in formules_q_incluses:
        debits['Mac-Math'] = debits_macmath(
            params['K_macmath'], bv_model.surface, pente, pj24h
        )
    if 'Fuller II' in formules_q_incluses:
        debits['Fuller II'] = debits_fuller2(
            params['A_fuller'], params['N_fuller'], bv_model.surface, PERIODES
        )
    if 'Mallet-Gauthier' in formules_q_incluses:
        debits['Mallet-Gauthier'] = debits_mallet_gauthier(
            params['k_mallet'], params['a_mallet'],
            sp_model.hauteur_moyenne, bv_model.surface, bv_model.thalweg, PERIODES,
        )
    if 'Hazen-Lazervic' in formules_q_incluses:
        debits['Hazen-Lazervic'] = debits_hazen_lazervic(
            params['K1_hl'], params['K2_hl'],
            bv_model.surface,
            pj24h.get(10, 0),
            sp_model.grad_exp_pluie,
            params['a_hl'],
            PERIODES,
        )
    if sh_obj and sh_obj.qj and 'Francou-Rodier' in formules_q_incluses:
        debits['Francou-Rodier'] = debits_francou_rodier(
            sh_obj, bv_model.surface, PERIODES
        )

    # ── (E) Q10 référence (sans Fuller II) ──────────────────────────────
    Q10_ref = estimer_q10_gradex(
        debits,
        formules_retenues=[k for k in debits if 'fuller' not in k.lower()],
        verbose=False,
    )

    # ── (F) Méthode du Gradex ────────────────────────────────────────────
    debits_gradex = methode_gradex(
        Q10_ref, sp_model.grad_exp_pluie,
        bv_model.surface, Tc_h,
        periodes=PERIODES, verbose=False,
    )

    # ── (G) Résultats finaux — formules choisies par l'utilisateur ────────
    # L'utilisateur choisit les formules INCLUSES ; on déduit les exclues.
    formules_exclues = [
        f for f in FORMULES_Q_DISPONIBLES if f not in formules_q_incluses
    ]
    q_finaux = resultats_finaux(
        debits, debits_gradex,
        formules_exclues=formules_exclues,
        periodes_cibles=PERIODES,
        verbose=False,
    )

    return {
        # Temps de concentration
        'tc':    {k: round(v, 3) for k, v in tc.items()},
        'Tc_min': round(Tc_min, 3),
        'Tc_h':   round(Tc_h,   4),
        'formules_tc_incluses': formules_tc,
        # Intensités Montana
        'intensites': {T: round(v, 5) for T, v in intensites.items()},
        # Pluies
        'pj24h': pj24h,
        'pente_pct': round(pente * 100, 4),
        # Débits par formule : {nom: {T: Q}}
        'debits': {
            nom: {T: round(q, 3) for T, q in qd.items()}
            for nom, qd in debits.items()
        },
        # Gradex
        'Q10_gradex':   round(Q10_ref, 3),
        'debits_gradex': {T: round(v, 3) for T, v in debits_gradex.items()},
        # Résultats finaux
        'q_finaux':          {T: round(v, 3) for T, v in q_finaux.items()},
        'formules_q_incluses': formules_q_incluses,
        # Infos stations utilisées
        'station_pluvio': sp_model.nom,
        'station_hydro':  sh_model.nom if sh_model else '—',
        'station_hydro_id': sh_model.pk if sh_model else None,
        'station_hydro_nom': sh_model.nom if sh_model else '—',
        # Paramètres stockés pour permettre le recalcul (personnalisation)
        'montana_a':   a_list,
        'montana_b':   b_list,
        'surface':     bv_model.surface,
        'grad_exp_pluie': sp_model.grad_exp_pluie,
        'C_rationnel': params['C_rationnel'],
        'K_macmath':   params['K_macmath'],
        'A_fuller':    params['A_fuller'],
        'N_fuller':    params['N_fuller'],
        'k_mallet':    params['k_mallet'],
        'a_mallet':    params['a_mallet'],
        'K1_hl':       params['K1_hl'],
        'K2_hl':       params['K2_hl'],
        'a_hl':        params['a_hl'],
    }


# =============================================================================
# Fonctions de recalcul pour la personnalisation (AJAX)
# =============================================================================

def _debits_int_keys(dc):
    """Reconstruit le dict débits avec clés entières depuis details_calcul."""
    result = {}
    for formule, qd in dc.get('debits', {}).items():
        result[formule] = {int(k): v for k, v in qd.items()}
    return result


def recalculer_depuis_tc(dc, formules_tc_incluses):
    """
    Recalcule intensités, débits et résultats finaux depuis une nouvelle
    sélection de formules Tc.

    dc                  : details_calcul dict (stocké en base)
    formules_tc_incluses: list[str] — formules dont on fait la moyenne
    """
    tc_dict = dc.get('tc', {})
    tc_vals = [v for k, v in tc_dict.items()
               if k != 'Moyenne' and k in formules_tc_incluses]
    if not tc_vals:
        return None

    Tc_min = sum(tc_vals) / len(tc_vals)
    Tc_h   = Tc_min / 60.0

    a_list = dc.get('montana_a', [])
    b_list = dc.get('montana_b', [])
    if not a_list or not b_list:
        return None

    intensites_new = intensites_montana(a_list, b_list, Tc_min, PERIODES)

    C       = dc.get('C_rationnel', 0.42)
    surface = dc.get('surface', 0.0)
    rat_new = debits_rationnels(C, intensites_new, surface)

    debits = _debits_int_keys(dc)
    debits['Rationnelle'] = rat_new

    formules_q_incluses = dc.get('formules_q_incluses', list(debits.keys()))
    Q10_ref = estimer_q10_gradex(
        debits,
        formules_retenues=[k for k in formules_q_incluses
                           if 'fuller' not in k.lower() and k in debits],
        verbose=False,
    )

    gradex        = dc.get('grad_exp_pluie', 0.0)
    debits_gradex = methode_gradex(
        Q10_ref, gradex, surface, Tc_h, periodes=PERIODES, verbose=False,
    )

    formules_exclues = [f for f in FORMULES_Q_DISPONIBLES
                        if f not in formules_q_incluses]
    q_finaux = resultats_finaux(
        debits, debits_gradex,
        formules_exclues=formules_exclues,
        periodes_cibles=PERIODES,
        verbose=False,
    )

    return {
        'Tc_min':   round(Tc_min, 3),
        'Tc_h':     round(Tc_h, 4),
        'intensites': {T: round(v, 5) for T, v in intensites_new.items()},
        'debits':     {nom: {T: round(q, 3) for T, q in qd.items()}
                       for nom, qd in debits.items()},
        'Q10_gradex':    round(Q10_ref, 3),
        'debits_gradex': {T: round(v, 3) for T, v in debits_gradex.items()},
        'q_finaux':      {T: round(v, 3) for T, v in q_finaux.items()},
    }


def recalculer_depuis_formules_q(dc, formules_q_incluses):
    """
    Recalcule Q10_ref, Gradex et q_finaux depuis une nouvelle sélection
    de formules Q.

    dc                  : details_calcul dict
    formules_q_incluses : list[str] — formules dont on fait la moyenne
    """
    # Reconstruire uniquement les débits des formules sélectionnées
    all_debits = _debits_int_keys(dc)
    debits = {
        nom: qd for nom, qd in all_debits.items()
        if nom in formules_q_incluses
    }

    Q10_ref = estimer_q10_gradex(
        debits,
        formules_retenues=[k for k in formules_q_incluses
                           if 'fuller' not in k.lower() and k in debits],
        verbose=False,
    )

    gradex   = dc.get('grad_exp_pluie', 0.0)
    surface  = dc.get('surface', 0.0)
    Tc_h     = dc.get('Tc_h', 0.0)
    debits_gradex = methode_gradex(
        Q10_ref, gradex, surface, Tc_h, periodes=PERIODES, verbose=False,
    )

    formules_exclues = [f for f in FORMULES_Q_DISPONIBLES
                        if f not in formules_q_incluses]
    q_finaux = resultats_finaux(
        debits, debits_gradex,
        formules_exclues=formules_exclues,
        periodes_cibles=PERIODES,
        verbose=False,
    )

    return {
        'Q10_gradex':         round(Q10_ref, 3),
        'debits_gradex':      {T: round(v, 3) for T, v in debits_gradex.items()},
        'q_finaux':           {T: round(v, 3) for T, v in q_finaux.items()},
        'formules_q_incluses': formules_q_incluses,
    }


# =============================================================================
# Apports de crue sans prelevement
# =============================================================================

def _hydrogramme_nash_brut(t: float, Tc: float, Qp: float) -> float:
    """Hydrogramme de Nash brut, sans limitation de debit."""
    if Tc <= 0 or Qp <= 0:
        return 0.0
    try:
        x = t / Tc
        if x < 0:
            return 0.0
        return Qp * (x ** 4) * math.exp(4.0 - 4.0 * x)
    except (OverflowError, ValueError):
        return 0.0


def _volume_crue_brut(Qp: float, Tc: float, frequence_mois: float, n_steps: int = 1000) -> float:
    """Volume d'une crue sans cap de prelevement, puis multiplie par la frequence mensuelle."""
    if Qp <= 0 or Tc <= 0 or frequence_mois <= 0:
        return 0.0

    a, b_lim = 0.0, 4.0 * Tc
    h = (b_lim - a) / n_steps
    f = lambda t: _hydrogramme_nash_brut(t, Tc, Qp)
    somme = (f(a) + f(b_lim)) / 2.0
    for i in range(1, n_steps):
        somme += f(a + i * h)
    return somme * h * 3600.0 * frequence_mois


def transposer_francou_rodier(debits_m3s, S_cible_km2, S_jauge_km2):
    """Transpose des débits de pointe du BV jaugé vers un BV cible (Francou-Rodier).

    Pour chaque débit observé `Q` sur le BV jaugé (surface `S_jauge`), on déduit
    le coefficient k de Francou-Rodier, puis on l'applique à la surface du BV
    cible (`S_cible`) :

        k       = 10·(1 − (log10(Q) − 6) / (log10(S_jauge) − 8))
        Q_cible = 10^6 · (S_cible / 10^8)^(1 − k/10)

    NB : miroir de `Besions_Ressources.calculs._debits_francou_rodier`
    (garder les deux en cohérence).
    """
    log_S_jauge = math.log10(max(float(S_jauge_km2 or 0.0), 1e-6))
    denom = log_S_jauge - 8.0
    out = []
    for Q in debits_m3s:
        Q = float(Q or 0.0)
        if Q <= 0 or denom == 0:
            out.append(0.0 if Q <= 0 else Q)
            continue
        k = 10.0 * (1.0 - (math.log10(max(Q, 1e-6)) - 6.0) / denom)
        Q_cible = 1e6 * (max(float(S_cible_km2 or 0.0), 1e-6) / 1e8) ** (1.0 - k / 10.0)
        out.append(Q_cible)
    return out


def calculer_apports_crue_sans_prelevement(station_hydro, tc_h: Optional[float],
                                           surface_bv_km2: Optional[float] = None) -> Dict:
    """Retourne les apports de crue bruts par type d'annee, sans prelevement.

    Les débits de pointe mensuels observés à la station (BV jaugé) sont d'abord
    **transposés par Francou-Rodier** vers le BV cible (`surface_bv_km2`) à partir
    de la surface jaugée de la station, avant l'intégration de l'hydrogramme de
    Nash. Si `surface_bv_km2` ou la surface jaugée est absente, les débits
    observés sont utilisés tels quels (pas de transposition).

    Le resultat est structure pour un graphe unique avec 3 scenarios:
    normale, humide et seche.
    """
    tc_h = float(tc_h or 0.0)
    s_jauge = getattr(station_hydro, 'superficie_bv_jaugee', None) if station_hydro else None
    transpose = bool(surface_bv_km2 and s_jauge)

    def _serie(annee_type: str) -> Dict:
        debits = list(getattr(station_hydro, f'debits_mensuels_annee_{annee_type}') or []) if station_hydro else []
        frequences = list(getattr(station_hydro, f'frequences_mensuelles_annee_{annee_type}') or []) if station_hydro else []
        if len(debits) != 12:
            debits = [0.0] * 12
        if len(frequences) != 12:
            frequences = [0.0] * 12

        debits_obs = [float(qp or 0.0) for qp in debits]
        debits_calc = transposer_francou_rodier(debits_obs, surface_bv_km2, s_jauge) if transpose else debits_obs

        volumes = [
            round(_volume_crue_brut(float(qp or 0.0), tc_h, float(freq or 0.0)), 3)
            for qp, freq in zip(debits_calc, frequences)
        ]
        return {
            'debits_observes_m3s': [round(q, 3) for q in debits_obs],
            'debits_m3s':          [round(q, 3) for q in debits_calc],   # transposés (= utilisés)
            'frequences':          [round(float(freq or 0.0), 3) for freq in frequences],
            'volumes_m3':          volumes,
            'total_m3':            round(sum(volumes), 3),
        }

    return {
        'mois': MOIS_SEP_AOU,
        'tc_h': round(tc_h, 4),
        'transposition':      transpose,
        'surface_bv_km2':     surface_bv_km2,
        'surface_jaugee_km2': s_jauge,
        'normale': _serie('normale'),
        'humide':  _serie('humide'),
        'seche':   _serie('seche'),
    }
