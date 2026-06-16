"""Logique de calcul pour le bilan besoins-ressources.
Calendrier hydrologique : Septembre → Août (12 mois).
"""

import math
from typing import List, Dict, Optional

MOIS_SEP_AOU = ["Sep", "Oct", "Nov", "Déc", "Jan", "Fév", "Mar", "Avr", "Mai", "Jui", "Jul", "Aoû"]
JOURS_MOIS_STD = [30, 31, 30, 31, 31, 28, 31, 30, 31, 30, 31, 31]

INSOLATION_TABLE = {
    # n/N mensuel (Sep -> Aoû), selon latitude (degrés)
  20.0: [0.28, 0.26, 0.25, 0.25, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.30, 0.29],
    25.0: [0.28, 0.26, 0.25, 0.24, 0.24, 0.26, 0.27, 0.29, 0.30, 0.31, 0.31, 0.29],
    30.0: [0.28, 0.26, 0.24, 0.23, 0.24, 0.25, 0.27, 0.29, 0.31, 0.32, 0.31, 0.30],
    32.0: [0.28, 0.26, 0.24, 0.23, 0.23, 0.25, 0.27, 0.29, 0.31, 0.32, 0.32, 0.30],
    34.0: [0.28, 0.25, 0.23, 0.22, 0.23, 0.25, 0.27, 0.29, 0.31, 0.32, 0.32, 0.30],
    35.0: [0.28, 0.25, 0.23, 0.22, 0.23, 0.25, 0.27, 0.29, 0.31, 0.32, 0.32, 0.30],
    40.0: [0.28, 0.25, 0.22, 0.21, 0.22, 0.24, 0.27, 0.30, 0.32, 0.34, 0.33, 0.31],
}


def _interpole_table_latitude(latitude: float, table: Dict[float, List[float]]) -> List[float]:
    """Interpolation linéaire des 12 valeurs mensuelles selon la latitude."""
    lats = sorted(table.keys())
    if latitude <= lats[0]:
        return list(table[lats[0]])
    if latitude >= lats[-1]:
        return list(table[lats[-1]])

    for i in range(len(lats) - 1):
        lo, hi = lats[i], lats[i + 1]
        if lo <= latitude <= hi:
            t = (latitude - lo) / (hi - lo)
            return [
                round(table[lo][m] + t * (table[hi][m] - table[lo][m]), 2)
                for m in range(12)
            ]
    return list(table[lats[0]])


def taux_insolation_par_latitude(latitude: float) -> List[float]:
    """Retourne n/N (12 mois Sep->Aoû) depuis la latitude en degrés."""
    return _interpole_table_latitude(latitude, INSOLATION_TABLE)


# ─── ETo ────────────────────────────────────────────────────────────────────

def calculer_eto(temperatures: List[float], taux_insolation: List[float], latitude: float) -> Dict:
    """ETo mensuel par méthode Hargreaves simplifiée. Retourne dict de résultats."""
    eto_mm_j, eto_mm_mois = [], []
    for i in range(12):
        t_moy = temperatures[i]
        n_n = taux_insolation[i]
        kt = 0.031 * math.sqrt(max(t_moy, 0.0)) + 0.24
        eto_j = n_n * kt * (0.457 * t_moy + 8.13)
        eto_mm_j.append(round(eto_j, 2))
        eto_mm_mois.append(round(eto_j * JOURS_MOIS_STD[i], 1))
    return {
        'mois': MOIS_SEP_AOU,
        'eto_mm_j': eto_mm_j,
        'eto_mm_mois': eto_mm_mois,
        'temperatures': [round(t, 1) for t in temperatures],
        'taux_insolation': [round(n, 2) for n in taux_insolation],
    }


def pluie_efficace(precipitations: List[float]) -> List[float]:
    result = []
    for p in precipitations:
        result.append(round(0.60 * p if p < 75 else 0.80 * p, 1))
    return result


# ─── Besoins cultures ────────────────────────────────────────────────────────

def calculer_besoins_culture(
    nom: str,
    kc: List[float],
    kr: List[float],
    superficie_ha: float,
    efficiance: float,
    eto_mm_j: List[float],
    pluie_eff: List[float],
) -> Dict:
    """Besoins mensuels bruts et réels pour une culture."""
    etc_mm_j, bruts_mm_j, reel_mm_j = [], [], []
    bruts_m3, reel_m3 = [], []
    for i in range(12):
        etc = eto_mm_j[i] * kc[i] * kr[i]
        brut_j = etc / 0.9 if efficiance else 0.0
        # pluie_eff est en mm/mois → diviser par jours pour mm/j
        reel_j = max(0.0, brut_j - pluie_eff[i] / JOURS_MOIS_STD[i])
        j = JOURS_MOIS_STD[i]
        etc_mm_j.append(round(etc, 2))
        bruts_mm_j.append(round(brut_j, 2))
        reel_mm_j.append(round(reel_j, 2))
        bruts_m3.append(round(brut_j * superficie_ha * 10.0 * j, 0))
        reel_m3.append(round(reel_j * superficie_ha * 10.0 * j, 0))
    return {
        'nom': nom,
        'mois': MOIS_SEP_AOU,
        'etc_mm_j': etc_mm_j,
        'besoins_bruts_mm_j': bruts_mm_j,
        'besoins_reel_mm_j': reel_mm_j,
        'besoins_bruts_m3_mois': bruts_m3,
        'besoins_reel_m3_mois': reel_m3,
    }


def besoins_globaux_m3(cultures_results: List[Dict]) -> List[float]:
    total = [0.0] * 12
    for c in cultures_results:
        for i in range(12):
            total[i] += c['besoins_bruts_m3_mois'][i]
    return total


# ─── Ressource Crues (Francou-Rodier + Manning + hydrogramme Nash) ───────────

def _sep_aou_to_jan_dec(v: List[float]) -> List[float]:
    return [v[4], v[5], v[6], v[7], v[8], v[9], v[10], v[11], v[0], v[1], v[2], v[3]]


def _jan_dec_to_sep_aou(v: List[float]) -> List[float]:
    return [v[8], v[9], v[10], v[11], v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7]]


def _debits_francou_rodier(debits_m3s: List[float], S_km2: float, S_jauge_km2: float) -> List[float]:
    log_S_jauge = math.log10(max(S_jauge_km2, 1e-6))
    resultats = []
    for Q in debits_m3s:
        if Q <= 0:
            resultats.append(0.0)
            continue
        k_T = 10.0 * (1.0 - (math.log10(max(Q, 1e-6)) - 6.0) / (log_S_jauge - 8.0))
        Q_T = 1e6 * (S_km2 / 1e8) ** (1.0 - k_T / 10.0)
        resultats.append(Q_T)
    return resultats


def _canal_trapezoidal(b: float, y: float, z: float, pente: float, n: float) -> float:
    A = (b + z * y) * y
    P = b + 2 * y * math.sqrt(1 + z ** 2)
    if P == 0 or n == 0 or pente <= 0:
        return 0.0
    R = A / P
    return (1.0 / n) * A * (R ** (2.0 / 3.0)) * math.sqrt(pente)


def _canal_circulaire(diametre: float, y: float, pente: float, n: float) -> float:
    """Capacité Manning pour une conduite circulaire partiellement pleine.

    diametre : D (m), y : hauteur d'eau (m), pente : i (m/m), n : Manning.
    θ = 2·acos(1 − 2y/D)  →  A = D²/8·(θ − sin θ),  P = D·θ/2,  R = A/P.
    Si y ≥ D, on assimile à la section pleine (θ = 2π).
    """
    if diametre is None or diametre <= 0 or y is None or y <= 0 or n == 0 or pente <= 0:
        return 0.0
    ratio = min(max(y / diametre, 0.0), 1.0)
    if ratio >= 1.0:
        theta = 2.0 * math.pi
    else:
        theta = 2.0 * math.acos(1.0 - 2.0 * ratio)
    A = (diametre ** 2) / 8.0 * (theta - math.sin(theta))
    P = diametre * theta / 2.0
    if P == 0:
        return 0.0
    R = A / P
    return (1.0 / n) * A * (R ** (2.0 / 3.0)) * math.sqrt(pente)


def _capacite_troncon(forme: str, params: dict) -> float:
    """Dispatcher de capacité Manning selon la forme du tronçon.

    Formes supportées :
      - 'trapezoidale'  → b, y, z, pente, n
      - 'rectangulaire' → b, y, pente, n (z = 0 implicite)
      - 'circulaire'    → diametre, y, pente, n
    """
    pente = params.get('pente') or 0.0
    n = params.get('n') or 0.0
    y = params.get('y') or 0.0
    if forme == 'circulaire':
        return _canal_circulaire(params.get('diametre') or 0.0, y, pente, n)
    z = params.get('z') if forme == 'trapezoidale' else 0.0
    b = params.get('b') or 0.0
    return _canal_trapezoidal(b, y, z or 0.0, pente, n)


def _hydrogramme_nash(t: float, Tc: float, Qp: float, Qdmax: float) -> float:
    if Tc <= 0:
        return 0.0
    try:
        Q = Qp * (t / Tc) ** 4 * math.exp(4.0 - 4.0 * (t / Tc))
        return min(Q, Qdmax)
    except (OverflowError, ValueError):
        return 0.0


def _integrale_trapeze(Qp: float, Tc: float, Qdmax: float, frequence_mois: float, n_steps: int = 1000) -> float:
    """Volume mensuel (m³) apporté par les crues d'un mois donné.

    Intègre l'hydrogramme de Nash (1 crue) sur [0, 4·Tc] en secondes pour obtenir
    le volume d'UNE crue (m³), puis multiplie par `frequence_mois` = nombre de
    crues sur le mois (issu de StationHydrometrique.frequences_mensuelles_annee_*).

    Ce paramètre n'est PAS le nombre de jours du mois.
    """
    a, b_lim = 0.0, 4.0 * Tc 
    h = (b_lim - a) / n_steps
    f = lambda t: _hydrogramme_nash(t, Tc , Qp, Qdmax)
    somme = (f(a) + f(b_lim)) / 2.0
    for i in range(1, n_steps):
        somme += f(a + i * h)
    return somme * h *3600* frequence_mois


def calculer_ressource_crue(
    tc_h: float,
    b1: Optional[float],
    y1: float,
    z1: Optional[float],
    pente1: float,
    manning_n1: float,
    debits_m3s_sep_aou: List[float],
    frequences_mois_sep_aou: List[float],
    sup_bv_km2: float,
    sup_jaugee_km2: float,
    b2: Optional[float] = None,
    y2: Optional[float] = None,
    z2: Optional[float] = None,
    pente2: Optional[float] = None,
    manning_n2: Optional[float] = None,
    coeff_humide: float = 1.30,
    forme1: str = 'trapezoidale',
    forme2: Optional[str] = None,
    diametre1: Optional[float] = None,
    diametre2: Optional[float] = None,
) -> Dict:
    """Calcule les apports de crue mensuels (m³) — normale et humide.

    Le 1er tronçon est obligatoire ; le 2e (params _2) est optionnel : un seuil
    peut avoir 1 ou 2 tronçons d'amenée, une prise locale en a 1. Qdmax est la
    somme des capacités max des tronçons fournis.

    `frequences_mois_sep_aou` (12 valeurs Sep→Aoû) : fréquence mensuelle des
    crues issue de StationHydrometrique.frequences_mensuelles_annee_* (nombre
    d'événements de crue par mois). Ce n'est PAS le nombre de jours du mois.

    Forme de section par tronçon (`forme1`, `forme2`) :
      - 'trapezoidale'  → utilise b, y, z, pente, manning
      - 'rectangulaire' → utilise b, y, pente, manning (z = 0)
      - 'circulaire'    → utilise diametre, y, pente, manning (b/z ignorés)
    """
    debits_jan_dec = _sep_aou_to_jan_dec(debits_m3s_sep_aou)
    frequences_jan_dec = _sep_aou_to_jan_dec(frequences_mois_sep_aou)
    Qi_jan_dec = _debits_francou_rodier(debits_jan_dec, sup_bv_km2, sup_jaugee_km2)
    Qdmax = _capacite_troncon(forme1, {
        'b': b1, 'y': y1, 'z': z1, 'pente': pente1, 'n': manning_n1,
        'diametre': diametre1,
    })
    troncon2_defini = (
        (forme2 == 'circulaire' and diametre2 is not None and y2 is not None
         and pente2 is not None and manning_n2 is not None)
        or (forme2 in ('trapezoidale', 'rectangulaire')
            and all(v is not None for v in (b2, y2, pente2, manning_n2)))
    )
    if troncon2_defini:
        Qdmax += _capacite_troncon(forme2, {
            'b': b2, 'y': y2, 'z': z2, 'pente': pente2, 'n': manning_n2,
            'diametre': diametre2,
        })

    volumes_jan_dec = []
    for i in range(12):
        freq = max(float(frequences_jan_dec[i] or 0.0), 0.0)
        vol = _integrale_trapeze(Qi_jan_dec[i], tc_h, Qdmax, freq)
        volumes_jan_dec.append(vol)

    vols_sep_aou = _jan_dec_to_sep_aou(volumes_jan_dec)
    debits_transp = _jan_dec_to_sep_aou(Qi_jan_dec)

    return {
        'mois': MOIS_SEP_AOU,
        'volumes_normale_m3': [round(v, 0) for v in vols_sep_aou],
        'volumes_humide_m3': [round(v * coeff_humide, 0) for v in vols_sep_aou],
        'qdmax_m3s': round(Qdmax, 3),
        'debits_transposes_m3s': [round(q, 2) for q in debits_transp],
    }


def hydrogramme_detail(Qp: float, Tc: float, Qdmax: float, n_pts: int = 100) -> Dict:
    """Points du hydrogramme de crue pour affichage graphique."""
    t_max = 4.0 * Tc
    t_pts = [round(k * t_max / (n_pts - 1), 3) for k in range(n_pts)]
    q_pts = [round(_hydrogramme_nash(t, Tc, Qp, Qdmax), 3) for t in t_pts]
    return {'t': t_pts, 'Q': q_pts}


# ─── Temps de concentration depuis le BV ─────────────────────────────────────

def calculer_tc_pour_bv(bv_model) -> Optional[Dict]:
    """Retourne le Tc (en heures) pour un bassin versant.

    1. Si une analyse hydrologique existe pour ce BV, prend le `temps_concentration`
       de l'analyse la plus récente.
    2. Sinon, calcule Tc via toutes les méthodes disponibles dans
       `analyse_hydrologique.calculs` et fait la moyenne.

    Retourne `{'tc_h': float, 'source': 'analyse'|'moyenne', 'details': {...}}`
    ou None si Tc n'est pas calculable (données BV incomplètes).
    """
    if bv_model is None:
        return None

    from analyse_hydrologique.models import ResultatAnalyseHydrologique

    analyse = (
        ResultatAnalyseHydrologique.objects
        .filter(bassin_versant=bv_model, temps_concentration__isnull=False)
        .order_by('-date_analyse')
        .first()
    )
    if analyse and analyse.temps_concentration:
        # ResultatAnalyseHydrologique.temps_concentration est stocké en MINUTES
        # (cf. analyse_hydrologique.views ligne 729 : `Tc_min`). Conversion → heures.
        return {
            'tc_h': round(float(analyse.temps_concentration) / 60.0, 4),
            'source': 'analyse',
            'details': {
                'analyse_id': analyse.id,
                'methode': analyse.methode,
                'tc_min': float(analyse.temps_concentration),
            },
        }

    # Fallback : moyenne des formules
    try:
        from analyse_hydrologique.calculs import bv_to_hydro, FORMULES_TC_DISPONIBLES
        from hydrologie_bv import calculer_tc_bv
    except Exception:
        return None

    try:
        bv_obj = bv_to_hydro(bv_model)
        tc = calculer_tc_bv(bv_obj, FORMULES_TC_DISPONIBLES, verbose=False)
        tc_min = tc.get('Moyenne')
        if tc_min is None:
            return None
        return {
            'tc_h': round(tc_min / 60.0, 4),
            'source': 'moyenne',
            'details': {k: round(v, 3) for k, v in tc.items()},
        }
    except Exception:
        return None


# ─── Autres ressources ────────────────────────────────────────────────────────

def apport_puits(debit_m3h: float, heures_j: float) -> List[float]:
    apport_j = debit_m3h * heures_j
    return [round(apport_j * j, 0) for j in JOURS_MOIS_STD]


def apport_khettara(debit_normal: List[float], debit_humide: List[float], annee_humide: bool) -> List[float]:
    debits = debit_humide if annee_humide else debit_normal
    return [round(q * j, 0) for q, j in zip(debits, JOURS_MOIS_STD)]


def apport_source(debit_normal: List[float], debit_humide: List[float], annee_humide: bool) -> List[float]:
    debits = debit_humide if annee_humide else debit_normal
    return [round(q * j, 0) for q, j in zip(debits, JOURS_MOIS_STD)]


def apport_barrage(lachers_normal: List[float], lachers_humide: List[float], annee_humide: bool) -> List[float]:
    return [round(v, 0) for v in (lachers_humide if annee_humide else lachers_normal)]


def apport_autre(debit_normal: List[float], debit_humide: List[float], annee_humide: bool) -> List[float]:
    debits = debit_humide if annee_humide else debit_normal
    return [round(q * j, 0) for q, j in zip(debits, JOURS_MOIS_STD)]


def calculer_apports_ressource(res: Dict, annee_humide: bool = False) -> List[float]:
    """Calcule les apports mensuels d'une ressource selon son type."""
    typ = res.get('type', '')
    if typ == 'puits':
        return apport_puits(res['debit_m3h'], res['heures_j'])
    if typ == 'khettara':
        return apport_khettara(res['debit_normal'], res.get('debit_humide', res['debit_normal']), annee_humide)
    if typ == 'barrage':
        return apport_barrage(res['lachers_normal'], res.get('lachers_humide', res['lachers_normal']), annee_humide)
    if typ == 'source':
        return apport_source(res['debit_normal'], res.get('debit_humide', res['debit_normal']), annee_humide)
    if typ == 'autre':
        return apport_autre(res['debit_normal'], res.get('debit_humide', res['debit_normal']), annee_humide)
    return [0.0] * 12


# ─── Apports par ouvrage associé (modèle BilanOuvrageAssocie) ─────────────────
#
# Référence : explication utilisateur du 2026-05-19.
# Trois types d'année sont calculés : 'normale', 'humide', 'seche'.
# Pour chaque ouvrage, on retourne 12 valeurs (Sep→Aoû) en m³ après application
# de l'efficience du réseau.
#
# Sources de données :
#   - station hydrométrique : Qp = debits_mensuels_annee_<type> ;
#                             jours = frequences_mensuelles_annee_<type>
#   - BilanOuvrageAssocie    : efficience_reseau, debit_amont_m3s,
#                              capacite_deversement_pct, debit_troncon_m3s
#                              (= "débit de transfert"), tc_h,
#                              debit_khettarat_m3s, debit_transfert_m3s,
#                              transfert_amont, tour_eau_jours, duree_jours,
#                              coeff_humide, coeff_seche,
#                              apports_mensuels_<type> (m³, barrage)
#   - AutreRessource         : apports_mensuels_<type> (m³), efficience
# ─────────────────────────────────────────────────────────────────────────────

ANNEES_TYPES = ('normale', 'humide', 'seche')
SECONDES_JOUR = 86400


def _station_qp_frequences(station_hydro, annee_type: str):
    """Retourne (Qp[12], frequences[12]) depuis la station hydrométrique pour
    le type d'année demandé. À défaut, retombe sur normale puis sur 0.

    `frequences` = nombre de crues par mois (Sep→Aoû) issu de
    StationHydrometrique.frequences_mensuelles_annee_*. C'est ce qui multiplie
    le volume d'une crue (intégrale de Nash) pour obtenir le volume mensuel ;
    ce n'est PAS le nombre de jours calendaires du mois.
    """
    debits = []
    frequences = []
    if station_hydro is not None:
        debits = list(getattr(station_hydro, f'debits_mensuels_annee_{annee_type}') or [])
        frequences = list(getattr(station_hydro, f'frequences_mensuelles_annee_{annee_type}') or [])
        # Fallback sur 'normale' si la série demandée est vide
        if not debits:
            debits = list(getattr(station_hydro, 'debits_mensuels_annee_normale') or [])
        if not frequences:
            frequences = list(getattr(station_hydro, 'frequences_mensuelles_annee_normale') or [])
    if len(debits) != 12:
        debits = [0.0] * 12
    if len(frequences) != 12:
        # Aucune fréquence connue → 0 (volume mensuel nul) plutôt que des
        # jours calendaires, qui n'ont pas de sens physique ici.
        frequences = [0.0] * 12
    return debits, frequences


def apport_seuil(oa, station_hydro, annee_type: str) -> List[float]:
    """Apport mensuel (m³, Sep→Aoû) d'un seuil pour un type d'année donné.

    Un seuil a 1 ou 2 tronçons d'amenée. Les débits des deux tronçons sont
    sommés (canaux en parallèle).

    Formule (par mois) :
        apport_brut = max(0,
            _integrale_trapeze(Qp, Tc, Q_total, jours)
            - _integrale_trapeze(Qp, Tc, Q_amont, jours)
        )
        apport = apport_brut × efficience_reseau

    avec :
        Q_total = debit_transfert_1 + debit_transfert_2 + debit_amont
        Q_amont = debit_amont
        debit_transfert_i = debit_troncon_(i)_m3s (auto depuis tronçon d'amenée i)
        debit_amont       = oa.debit_amont_m3s (saisi par l'utilisateur, défaut 0)
    """
    Qp_list, freq_list = _station_qp_frequences(station_hydro, annee_type)
    # Transposition Francou-Rodier : débits de la station (BV jaugé) → BV de l'ouvrage
    _bv = getattr(oa, 'bassin_versant', None)
    _s_cible = getattr(_bv, 'surface', None) if _bv else None
    _s_jauge = getattr(station_hydro, 'superficie_bv_jaugee', None) if station_hydro else None
    if _s_cible and _s_jauge:
        Qp_list = _debits_francou_rodier(Qp_list, _s_cible, _s_jauge)
    tc = oa.tc_h or 1.0
    transfert_1 = oa.debit_troncon_m3s or 0.0
    transfert_2 = getattr(oa, 'debit_troncon_2_m3s', None) or 0.0
    amont = oa.debit_amont_m3s or 0.0
    eff = oa.efficience_reseau if oa.efficience_reseau is not None else 0.75

    Q_total = transfert_1 + transfert_2 + amont
    Q_amont = amont

    apports = []
    for i in range(12):
        Qp = Qp_list[i]
        freq = max(float(freq_list[i] or 0.0), 0.0)
        if Qp <= 0 or freq <= 0 or Q_total <= 0:
            apports.append(0.0)
            continue
        a_total = _integrale_trapeze(Qp, tc, Q_total, freq)
        a_amont = _integrale_trapeze(Qp, tc, Q_amont, freq) if Q_amont > 0 else 0.0
        brut = max(0.0, a_total - a_amont)
        apports.append(round(brut * eff, 3))
    return apports


def apport_prise_locale(oa, station_hydro, annee_type: str) -> List[float]:
    """Apport mensuel (m³, Sep→Aoû) d'une prise locale pour un type d'année.

    Formule (par mois) :
        Q_total = (capacite_deversement_pct / 100) × debit_transfert + debit_amont
        Q_amont = debit_amont
        apport_brut = max(0,
            _integrale_trapeze(Qp, Tc, Q_total, jours)
            - _integrale_trapeze(Qp, Tc, Q_amont, jours)
        )
        apport = apport_brut × efficience_reseau
    """
    Qp_list, freq_list = _station_qp_frequences(station_hydro, annee_type)
    # Transposition Francou-Rodier : débits de la station (BV jaugé) → BV de l'ouvrage
    _bv = getattr(oa, 'bassin_versant', None)
    _s_cible = getattr(_bv, 'surface', None) if _bv else None
    _s_jauge = getattr(station_hydro, 'superficie_bv_jaugee', None) if station_hydro else None
    if _s_cible and _s_jauge:
        Qp_list = _debits_francou_rodier(Qp_list, _s_cible, _s_jauge)
    tc = oa.tc_h or 1.0
    transfert = oa.debit_troncon_m3s or 0.0
    amont = oa.debit_amont_m3s or 0.0
    cap_pct = oa.capacite_deversement_pct if oa.capacite_deversement_pct is not None else 100.0
    eff = oa.efficience_reseau if oa.efficience_reseau is not None else 0.75

    Q_total = (cap_pct / 100.0) * transfert + amont
    Q_amont = amont

    apports = []
    for i in range(12):
        Qp = Qp_list[i]
        freq = max(float(freq_list[i] or 0.0), 0.0)
        if Qp <= 0 or freq <= 0 or Q_total <= 0:
            apports.append(0.0)
            continue
        a_total = _integrale_trapeze(Qp, tc, Q_total, freq)
        a_amont = _integrale_trapeze(Qp, tc, Q_amont, freq) if Q_amont > 0 else 0.0
        brut = max(0.0, a_total - a_amont)
        apports.append(round(brut * eff, 3))
    return apports


def apport_khettara_forage(oa, annee_type: str) -> List[float]:
    """Apport mensuel (m³, Sep→Aoû) d'une khettara ou d'un forage/puits.

    Formule (par mois) :
        debit = debit_transfert_m3s si transfert_amont sinon debit_khettarat_m3s
        coeff_annee = 1.0 (normale) | coeff_humide | coeff_seche
        apport_brut = debit × coeff_annee × (jours_mois / tour_eau_jours)
                            × (duree_jours × 86400)
        apport = apport_brut × efficience_reseau
    """
    debit = (oa.debit_transfert_m3s or 0.0) if oa.transfert_amont else (oa.debit_khettarat_m3s or 0.0)
    if annee_type == 'humide':
        coeff = oa.coeff_humide if oa.coeff_humide is not None else 1.30
    elif annee_type == 'seche':
        coeff = oa.coeff_seche if oa.coeff_seche is not None else 0.80
    else:
        coeff = 1.0
    cycle = oa.tour_eau_jours or 1.0
    duree_s = (oa.duree_jours or 30.5) * SECONDES_JOUR
    eff = oa.efficience_reseau if oa.efficience_reseau is not None else 0.75

    if debit <= 0 or cycle <= 0:
        return [0.0] * 12

    apports = []
    for i in range(12):
        fraction = JOURS_MOIS_STD[i] / cycle
        brut = debit * coeff * fraction * duree_s
        apports.append(round(brut * eff, 3))
    return apports


def apport_barrage(oa, annee_type: str) -> List[float]:
    """Apport mensuel (m³, Sep→Aoû) d'un barrage collinaire.

    L'utilisateur saisit directement les apports en m³ pour chaque type d'année.
    apport = valeur_saisie × efficience_reseau.
    """
    series = getattr(oa, f'apports_mensuels_{annee_type}', None) or []
    if not series:
        # Fallback : utiliser année normale si la série demandée est vide
        series = oa.apports_mensuels_normale or []
    if len(series) != 12:
        return [0.0] * 12
    eff = oa.efficience_reseau if oa.efficience_reseau is not None else 0.75
    return [round((v or 0.0) * eff, 3) for v in series]


def apport_autre_ressource(autre_res, annee_type: str) -> List[float]:
    """Apport mensuel (m³, Sep→Aoû) d'une "Autre ressource" (indépendante).

    Même logique qu'un barrage : valeurs saisies × efficience.
    """
    series = getattr(autre_res, f'apports_mensuels_{annee_type}', None) or []
    if not series:
        series = autre_res.apports_mensuels_normale or []
    if len(series) != 12:
        return [0.0] * 12
    eff = autre_res.efficience if autre_res.efficience is not None else 0.80
    return [round((v or 0.0) * eff, 3) for v in series]


def calculer_apports_ouvrage(oa, station_hydro, annee_type: str) -> List[float]:
    """Dispatcher : calcule les apports d'un BilanOuvrageAssocie selon son type.

    Retourne 12 valeurs en m³ (Sep→Aoû) pour le type d'année demandé.
    """
    if annee_type not in ANNEES_TYPES:
        raise ValueError(f"Type d'année inconnu : {annee_type!r} (attendu : {ANNEES_TYPES})")
    typ = oa.type_ouvrage
    if typ == 'seuil':
        return apport_seuil(oa, station_hydro, annee_type)
    if typ == 'prise_locale':
        return apport_prise_locale(oa, station_hydro, annee_type)
    if typ in ('khettara', 'forage'):
        return apport_khettara_forage(oa, annee_type)
    if typ == 'barrage':
        return apport_barrage(oa, annee_type)
    return [0.0] * 12


def calculer_apports_bilan(bilan, annee_type: str) -> Dict:
    """Calcule les apports mensuels (m³, Sep→Aoû) de tous les ouvrages associés
    et autres ressources d'un bilan pour un type d'année.

    Retourne :
        {
            'total_m3': [12 valeurs],
            'par_ouvrage': [
                {'id': ..., 'type': ..., 'nom': ..., 'apports_m3': [12]}
            ],
            'par_autre_ressource': [
                {'id': ..., 'nom': ..., 'apports_m3': [12]}
            ],
        }
    """
    station = bilan.station_hydrometrique
    total = [0.0] * 12
    par_ouvrage = []
    for oa in bilan.ouvrages_associes.all():
        apports = calculer_apports_ouvrage(oa, station, annee_type)
        for i in range(12):
            total[i] += apports[i]
        ouv = oa.ouvrage
        nom = getattr(ouv, 'nom', None) or getattr(ouv, 'nom_du_seuil', None) or str(oa)
        par_ouvrage.append({
            'id': oa.id,
            'type': oa.type_ouvrage,
            'nom': nom,
            'apports_m3': apports,
        })
    par_autre = []
    for res in bilan.autres_ressources_eau.all():
        apports = apport_autre_ressource(res, annee_type)
        for i in range(12):
            total[i] += apports[i]
        par_autre.append({
            'id': res.id,
            'nom': res.nom,
            'apports_m3': apports,
        })
    return {
        'annee_type': annee_type,
        'total_m3': [round(v, 3) for v in total],
        'par_ouvrage': par_ouvrage,
        'par_autre_ressource': par_autre,
    }


# ─── Bilan global ─────────────────────────────────────────────────────────────

def bilan_global(
    cultures_results: List[Dict],
    crue_volumes: List[float],
    autres_ressources: List[Dict],
    annee_humide: bool = False,
) -> Dict:
    besoins = besoins_globaux_m3(cultures_results)
    ressources = list(crue_volumes)

    ressources_detail = [{'nom': 'Crues', 'apports': list(crue_volumes)}]
    for res in (autres_ressources or []):
        apports = calculer_apports_ressource(res, annee_humide)
        for i in range(12):
            ressources[i] += apports[i]
        ressources_detail.append({'nom': res.get('nom', res['type']), 'apports': apports})

    bilan = [r - b for r, b in zip(ressources, besoins)]
    deficit = [max(0.0, -x) for x in bilan]
    excedent = [max(0.0, x) for x in bilan]

    return {
        'mois': MOIS_SEP_AOU,
        'besoins_m3': [round(b, 0) for b in besoins],
        'ressources_m3': [round(r, 0) for r in ressources],
        'bilan_m3': [round(x, 0) for x in bilan],
        'deficit_m3': [round(x, 0) for x in deficit],
        'excedent_m3': [round(x, 0) for x in excedent],
        'total_besoins': round(sum(besoins), 0),
        'total_ressources': round(sum(ressources), 0),
        'total_deficit': round(sum(deficit), 0),
        'total_excedent': round(sum(excedent), 0),
        'ressources_detail': ressources_detail,
    }
