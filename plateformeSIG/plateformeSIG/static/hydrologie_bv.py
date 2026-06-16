import math
from typing import List, Dict, Optional, Tuple

# =============================================================================
# 1. CLASSES PRINCIPALES
# =============================================================================

class StationPluviometrique:
    """
    Station pluviométrique avec données pluviologiques et statistiques.
    
    Paramètres
    ----------
    nom : str
        Nom de la station
    x, y : float
        Coordonnées Lambert (m)
    annees : list[int]
        Série des années d'observation
    pluie : list[float]
        Série des pluies journalières maximales annuelles (mm)
    pj24h : dict
        Pluie maximale 24h par période de retour {10: val, 20: val, 50: val, 100: val}
    gradex : float
        Gradex des pluies (mm) — paramètre de la loi de Gumbel
    hauteur_annuelle : float
        Hauteur moyenne annuelle de pluie (mm)
    """
    def __init__(
        self,
        nom: str,
        x: float,
        y: float,
        annees: List[int],
        pluie: List[float],
        pj24h: Dict[int, float],
        gradex: float,
        hauteur_annuelle: float
    ):
        self.nom = nom
        self.x = x
        self.y = y
        self.annees = annees
        self.pluie = pluie
        self.pj24h = pj24h           # {T: Pj(mm)} pour T=10,20,50,100
        self.gradex = gradex          # mm (loi de Gumbel)
        self.hauteur_annuelle = hauteur_annuelle  # mm/an

    def __repr__(self):
        return (f"StationPluviometrique(nom='{self.nom}', x={self.x}, y={self.y}, "
                f"n_obs={len(self.annees)}, gradex={self.gradex} mm, "
                f"Pj10={self.pj24h.get(10, '?')} mm)")


class StationHydrometrique:
    """
    Station hydrométrique avec séries de débits.

    Paramètres
    ----------
    nom : str
    x, y : float
        Coordonnées Lambert (m)
    annees : list[int]
    debit : list[float]
        Débits journaliers maximaux annuels (m³/s)
    superficie_jaugee : float
        Superficie du bassin jaugé (km²)
    qj : dict, optional
        Débits journaliers maximaux par période de retour {10: val, 20: val, 50: val, 100: val} (m³/s)
    """
    def __init__(
        self,
        nom: str,
        x: float,
        y: float,
        annees: List[int],
        debit: List[float],
        superficie_jaugee: float,
        qj: Optional[Dict[int, float]] = None
    ):
        self.nom = nom
        self.x = x
        self.y = y
        self.annees = annees
        self.debit = debit
        self.superficie_jaugee = superficie_jaugee
        self.qj = qj or {}      # {T: Qj(m³/s)} pour T=10,20,50,100

    def __repr__(self):
        return (f"StationHydrometrique(nom='{self.nom}', x={self.x}, y={self.y}, "
                f"n_obs={len(self.annees)}, S={self.superficie_jaugee} km²)")


class BassinVersant:
    """
    Bassin versant avec ses caractéristiques morphologiques.
    
    Paramètres
    ----------
    nom : str
    x_exutoire, y_exutoire : float
        Coordonnées de l'exutoire (m)
    superficie : float        km²
    perimetre : float         km
    zmin : float              altitude minimale (m NGM)
    zmax : float              altitude maximale (m NGM)
    z95 : float               altitude dépassée par 95% du BV (m) — optionnel
    z5 : float                altitude dépassée par 5% du BV (m) — optionnel
    longueur : float          longueur du plus grand parcours hydraulique (km)
    """
    def __init__(
        self,
        nom: str,
        x_exutoire: float,
        y_exutoire: float,
        superficie: float,
        perimetre: float,
        zmin: float,
        zmax: float,
        z95: float,
        z5: float,
        longueur: float
    ):
        self.nom = nom
        self.x_exutoire = x_exutoire
        self.y_exutoire = y_exutoire
        self.superficie = superficie     # km²
        self.perimetre = perimetre       # km
        self.zmin = zmin                 # m
        self.zmax = zmax                 # m
        self.z95 = z95                   # m (peut être None)
        self.z5 = z5                     # m (peut être None)
        self.longueur = longueur         # km

    # -------------------------------------------------------------------------
    # Dénivelé
    # -------------------------------------------------------------------------
    def denivele(self) -> float:
        """ΔH = Zmax − Zmin (m)"""
        return self.zmax - self.zmin

    def denivele_specifique(self) -> Optional[float]:
        """Ds = Z5% − Z95%  (m) — utilisé dans certaines formules"""
        if self.z95 is not None and self.z5 is not None:
            return self.z5 - self.z95
        return None

    # -------------------------------------------------------------------------
    # Pente
    # -------------------------------------------------------------------------
    def pente(self) -> float:
        """
        Pente principale (m/m) = ΔH / L  avec L en mètres.
        Utilisée dans les formules de temps de concentration.
        """
        return self.denivele() / (self.longueur * 1000.0)

    def pente_rectangle_equivalent(self) -> float:
        """
        Pente moyenne sur la longueur du rectangle équivalent (m/m).
        Utilisée dans la fiche morphologique du BV.
        """
        L_re, _ = self.rectangle_equivalent()
        return self.denivele() / (L_re * 1000.0)

    # -------------------------------------------------------------------------
    # Indice de Gravelius (Kc)
    # -------------------------------------------------------------------------
    def indice_gravelius(self) -> float:
        """
        Kc = 0.28 × P / √S   (P en km, S en km²)
        Valeur ≥ 1 ; plus Kc est élevé, plus le bassin est allongé.
        """
        return 0.28 * self.perimetre / math.sqrt(self.superficie)

    # -------------------------------------------------------------------------
    # Rapport de forme (dit ici "indice de Havan")
    # -------------------------------------------------------------------------
    def rapport_de_forme(self) -> float:
        """
        Rf = S / L²   (S en km², L en km)
        Aussi appelé facteur de forme ou indice de compacité de Havan
        dans certains ouvrages marocains.
        """
        return self.superficie / (self.longueur ** 2)

    # -------------------------------------------------------------------------
    # Rectangle équivalent
    # -------------------------------------------------------------------------
    def rectangle_equivalent(self) -> Tuple[float, float]:
        i=0.28 * self.perimetre / math.sqrt(self.superficie)
        P = self.perimetre
        S = self.superficie
        L =(i*S**0.5/1.12)*(1+(1-(1.12/i)**2)**0.5)
        l = (i*S**0.5/1.12)*(1-(1-(1.12/i)**2)**0.5)
        return L, l

    # -------------------------------------------------------------------------
    # Résumé
    # -------------------------------------------------------------------------
    def resume(self) -> str:
        L_re, l_re = self.rectangle_equivalent()
        lignes = [
            f"╔══ Bassin versant : {self.nom} ══",
            f"║  Exutoire        : X={self.x_exutoire}, Y={self.y_exutoire}",
            f"║  Superficie      : {self.superficie:.3f} km²",
            f"║  Périmètre       : {self.perimetre:.3f} km",
            f"║  Zmin / Zmax     : {self.zmin} / {self.zmax} m NGM",
            f"║  Dénivelé        : {self.denivele():.0f} m",
            f"║  Longueur        : {self.longueur:.3f} km",
            f"║  Pente (L)       : {self.pente()*100:.4f} %",
            f"║  Gravelius (Kc)  : {self.indice_gravelius():.4f}",
            f"║  Rapport de forme: {self.rapport_de_forme():.4f}",
            f"║  Rectangle éq.   : L={L_re:.3f} km  l={l_re:.3f} km",
            f"║  Pente (rec. éq.): {self.pente_rectangle_equivalent()*100:.4f} %",
            f"╚{'═'*40}",
        ]
        return "\n".join(lignes)

    def __repr__(self):
        return (f"BassinVersant(nom='{self.nom}', S={self.superficie} km², "
                f"L={self.longueur} km, ΔH={self.denivele()} m)")


# =============================================================================
# 2. SÉLECTION DE STATION DE RÉFÉRENCE
# =============================================================================

def distance_euclidienne(x1: float, y1: float, x2: float, y2: float) -> float:
    """Distance euclidienne entre deux points en coordonnées Lambert (m)."""
    return math.hypot(x2 - x1, y2 - y1)


def choisir_station_pluvio(
    bv: BassinVersant,
    stations: List[StationPluviometrique]
) -> StationPluviometrique:
    """
    Retourne la station pluviométrique la plus proche de l'exutoire du BV
    (distance euclidienne en coordonnées Lambert).
    """
    if not stations:
        raise ValueError("La liste de stations est vide.")
    station_ref = min(
        stations,
        key=lambda s: distance_euclidienne(
            bv.x_exutoire, bv.y_exutoire, s.x, s.y
        )
    )
    dist_km = distance_euclidienne(
        bv.x_exutoire, bv.y_exutoire, station_ref.x, station_ref.y
    ) / 1000.0
    print(f"  [Pluvio] Station sélectionnée : '{station_ref.nom}' "
          f"(distance = {dist_km:.2f} km)")
    return station_ref


def choisir_station_hydro(
    bv: BassinVersant,
    stations: List[StationHydrometrique]
) -> StationHydrometrique:
    """
    Retourne la station hydrométrique la plus proche de l'exutoire du BV.
    """
    if not stations:
        raise ValueError("La liste de stations est vide.")
    station_ref = min(
        stations,
        key=lambda s: distance_euclidienne(
            bv.x_exutoire, bv.y_exutoire, s.x, s.y
        )
    )
    dist_km = distance_euclidienne(
        bv.x_exutoire, bv.y_exutoire, station_ref.x, station_ref.y
    ) / 1000.0
    print(f"  [Hydro]  Station sélectionnée : '{station_ref.nom}' "
          f"(distance = {dist_km:.2f} km)")
    return station_ref


def station_referencePJ(
    bv: BassinVersant,
    stations: List[StationPluviometrique],
    methode: List[str]
) -> StationPluviometrique:
    if not stations:
        raise ValueError("La liste de stations est vide.")

    m = methode[0]
    if m == "plus proche":
        station_ref = min(
            stations,
            key=lambda s: distance_euclidienne(bv.x_exutoire, bv.y_exutoire, s.x, s.y)
        )
        dist_km = distance_euclidienne(
            bv.x_exutoire, bv.y_exutoire, station_ref.x, station_ref.y
        ) / 1000.0
        print(f"  [PJ] Méthode '{m}' → '{station_ref.nom}' (dist = {dist_km:.2f} km)")
    else:
        station_ref = stations[0]
        print(f"  [PJ] Méthode '{m}' → '{station_ref.nom}' (valeur directe)")

    return station_ref


def station_referenceQJ(
    bv: BassinVersant,
    stations: List[StationHydrometrique],
    methode: List[str]
) -> StationHydrometrique:
    if not stations:
        raise ValueError("La liste de stations est vide.")

    m = methode[0]
    if m == "plus proche":
        station_ref = min(
            stations,
            key=lambda s: distance_euclidienne(bv.x_exutoire, bv.y_exutoire, s.x, s.y)
        )
        dist_km = distance_euclidienne(
            bv.x_exutoire, bv.y_exutoire, station_ref.x, station_ref.y
        ) / 1000.0
        print(f"  [QJ] Méthode '{m}' → '{station_ref.nom}' (dist = {dist_km:.2f} km)")
    else:
        station_ref = stations[0]
        print(f"  [QJ] Méthode '{m}' → '{station_ref.nom}' (valeur directe)")

    return station_ref


# =============================================================================
# 3. TEMPS DE CONCENTRATION (Tc)
# =============================================================================
# Toutes les formules utilisent :
#   L   = longueur du plus grand parcours hydraulique (km)
#   S   = superficie du BV (km²)
#   J   = pente principale (m/m) = ΔH / L[m]
#   ΔH  = dénivelé total (m)
# Résultats en MINUTES sauf mention contraire.

def tc_kirpich(L_km: float, J: float) -> float:
    L_m = L_km * 1000.0
    return 0.01947 * (L_m ** 0.77) / (J ** 0.385)


def tc_turraza(L_km: float, S_km2: float, J: float) -> float:
    return (0.108 * ((L_km*S_km2)**(1/3)) /(J**0.5))*60


def tc_bransby_williams(L_km: float, S_km2: float, J: float) -> float:
    return 14.56* L_km / ((S_km2 ** 0.1) * (J ** 0.2))


def tc_van_te_chow(L_km: float, J: float) -> float:
    tc_h = 0.123*(L_km / J**0.5) ** 0.64
    return tc_h * 60.0


def tc_us_corps(L_km2: float, J: float) -> float:
    tc_h = 16.632*(L_km2/J**0.25)**0.76
    return tc_h 
def tc_californienne(L_km: float, J: float) -> float:
    tc_h = 8.712* (L_km / J **0.5) ** 0.77
    return tc_h 
def tc_espagnole(L_km: float, J: float) -> float:
    tc_h = 0.3 * ((L_km ** 0.76/ (J ** 0.19)) )
    return tc_h * 60.0
def tc_ventura(S_km2: float, J: float) -> float:
    tc_h = 76*math.sqrt(S_km2 / (J*100))
    return tc_h 
# Dictionnaire des formules disponibles
TC_FORMULES = {
    "Kirpich":         tc_kirpich,
    "Turraza":         tc_turraza,
    "Bransby":         tc_bransby_williams,
    "Van Te Chow":     tc_van_te_chow,
    "US Corps":        tc_us_corps,
    "Californienne":   tc_californienne,
    "Espagnole":       tc_espagnole,
    "Ventura":         tc_ventura,
}


def calculer_tc_bv(
    bv: BassinVersant,
    formules_choisies: Optional[List[str]] = None,
    verbose: bool = True
) -> Dict[str, float]:
    L   = bv.longueur         # km
    S   = bv.superficie       # km²
    J   = bv.pente()          # m/m
    dH  = bv.denivele()       # m

    if formules_choisies is None:
        formules_choisies = list(TC_FORMULES.keys())

    # Vérification des clés
    for f in formules_choisies:
        if f not in TC_FORMULES:
            raise ValueError(f"Formule inconnue : '{f}'. "
                             f"Choisir parmi : {list(TC_FORMULES.keys())}")

    resultats = {}
    for nom in formules_choisies:
        fn = TC_FORMULES[nom]
        if nom in ("Kirpich", "Californienne","US Corps","Van Te Chow", "Espagnole"):
            tc = fn(L, J)
        elif nom in ("Bransby","Turraza"):
            tc = fn(L, S, J)
        elif nom in ("Ventura"):
            tc = fn(S, J)
        else:
            tc = fn(L, J)
        resultats[nom] = tc

    # Moyenne des formules sélectionnées
    resultats["Moyenne"] = sum(resultats.values()) / len(resultats)

    if verbose:
        print(f"\n── Temps de concentration — BV : {bv.nom} ──")
        print(f"  L={L:.3f} km,  S={S:.3f} km²,  J={J*100:.4f}%,  ΔH={dH:.0f} m")
        print(f"  {'Formule':<20} {'Tc (min)':>12}  {'Tc (h)':>10}")
        print(f"  {'-'*45}")
        for nom, tc in resultats.items():
            print(f"  {nom:<20} {tc:>12.3f}  {tc/60:>10.4f}")
    return resultats


# =============================================================================
# 4. INTENSITÉ PLUVIEUSE — FORMULE DE MONTANA
# =============================================================================

def intensite_montana(
    a_mm_min: float,
    b: float,
    tc_min: float
) -> float:
    return a_mm_min * (tc_min ** (-b))


def intensites_montana(
    a_list: List[float],
    b_list: List[float],
    tc_min: float,
    periodes: List[int] = None
) -> Dict[int, float]:
    if periodes is None:
        periodes = [10, 20, 50, 100]
    if len(a_list) != len(periodes) or len(b_list) != len(periodes):
        raise ValueError("Les listes a, b et périodes doivent avoir la même longueur.")

    resultats = {}
    for T, a, b in zip(periodes, a_list, b_list):
        i_mm_h = intensite_montana(a, b, tc_min)
        resultats[T] = i_mm_h    #  SANS conversion mm/min → mm/h
    return resultats


# =============================================================================
# 5. DÉBITS DE POINTE — FORMULES EMPIRIQUES
# =============================================================================

# ── 5.1 Méthode rationnelle ──────────────────────────────────────────────────

def debit_rationnel(
    C: float,
    i_mm_h: float,
    S_km2: float
) -> float:
    return C * i_mm_h * S_km2 / 3.6


def debits_rationnels(
    C: float,
    intensites: Dict[int, float],
    S_km2: float
) -> Dict[int, float]:
    return {T: debit_rationnel(C, i, S_km2) for T, i in intensites.items()}


# ── 5.2 Formule de Mac-Math ──────────────────────────────────────────────────

def debits_macmath(
    K: float,
    S_km2: float,
    J: float,
    pj24h: Dict[int, float]
) -> Dict[int, float]:
    facteur =(K*(S_km2*100)**(0.58)*(J*100)**(0.42))*0.001
    return {T: facteur * pj for T, pj in pj24h.items()}

# ── 5.3 Formule de Fuller II ─────────────────────────────────────────────────
def debits_fuller2(
    A: float,
    N: int,
    S_km2: float,
    periodes: List[int] = None
) -> Dict[int, float]:
    if periodes is None:
        periodes = [10, 20, 50, 100]
    # Partie 1 : (S^0.8 + 8/3 * S^0.5)
    terme_surface = (S_km2 ** 0.8) + (8/3 * (S_km2 ** 0.5))
    # Partie 2 : (4/3 * N / 100)
    terme_fixe = (4/3) * (N / 100)
    
    resultats = {}
    
    for T in periodes:
        # On évite le log(0) au cas où
        if T <= 0:
            continue
            
        # Partie 3 : (1 + a * log10(T))
        facteur_temps = 1 + A * math.log10(T)
        
        # Calcul final : Q_T = (Facteur Temps) * (Terme Surface) * (Terme Fixe)
        Q_T = facteur_temps * terme_surface * terme_fixe
        
        resultats[T] = round(Q_T, 3) # Arrondi à 3 décimales pour la précision

    return resultats

# ── 5.4 Formule de Mallet-Gautier ───────────────────────────────────────────

def debits_mallet_gauthier(
    k: float,
    a: float,
    H: float,
    A_km2: float,
    L_km: float,
    periodes: List[int] = None
) -> Dict[int, float]:
    if periodes is None:
        periodes = [10, 20, 50, 100]

    terme_fixe = 2.0 * k * math.log10(1.0 + a * H*10**-3) * (A_km2 / math.sqrt(L_km))

    resultats = {}
    for T in periodes:
        val_sous_racine = 1.0 + 4.0 * math.log10(T) - math.log10(A_km2)
        if val_sous_racine < 0:
            raise ValueError(
                f"Terme sous la racine négatif pour T={T}, A={A_km2} km². "
                "Vérifier les paramètres."
            )
        Q = terme_fixe * math.sqrt(val_sous_racine)
        resultats[T] = Q
    return resultats


# ── 5.5 Formule de Hazen-Lazervic ────────────────────────────────────────────


def debits_hazen_lazervic(
    K1: float,
    K2: float,
    S_km2: float,
    pj24h_10: float,
    gradex_pluie: float,
    a_exp: float,
    periodes: List[int] = None
) -> Dict[int, float]:
    Q_1000 = K1 * (S_km2 ** K2)

    resultats = {}
    for T in periodes:
        Q = Q_1000 * ((1+a_exp*math.log10(T))/(1+a_exp*math.log10(1000)))
        resultats[T] = Q
    return resultats


# ── 5.6 Formule de Francou-Rodier (UFR) ──────────────────────────────────────

def debits_francou_rodier(
    station_hydro: 'StationHydrometrique',
    S_km2: float,
    periodes: List[int] = None
) -> Dict[int, float]:
    Q_ref = station_hydro.qj
    if periodes is None:
        periodes = list(Q_ref.keys())

    S_bv_m2     = S_km2                       
    S_jauge_m2  = station_hydro.superficie_jaugee 
    log_S_jauge = math.log10(S_jauge_m2)

    resultats = {}
    for T in periodes:
        if T not in Q_ref:
            continue
        k_T = 10.0 * (1.0 - (math.log10(Q_ref[T]) - 6.0) / (log_S_jauge - 8.0))
        print(k_T)
        Q_T = 1e6 * (S_bv_m2 / 1e8) ** (1.0 - k_T / 10.0)

        resultats[T] = Q_T
    return resultats


# =============================================================================
# 6. ESTIMATION Q10 — MOYENNE DES FORMULES
# =============================================================================

def estimer_q10_gradex(
    debits_par_formule: Dict[str, Dict[int, float]],
    formules_retenues: Optional[List[str]] = None,
    verbose: bool = True
) -> float:

    if formules_retenues is None:
        # Par défaut : toutes sauf Fuller II (valeurs souvent aberrantes)
        formules_retenues = [
            k for k in debits_par_formule
            if "fuller" not in k.lower()
        ]

    valeurs_q10 = []
    for nom in formules_retenues:
        if nom in debits_par_formule and 10 in debits_par_formule[nom]:
            valeurs_q10.append(debits_par_formule[nom][10])

    if not valeurs_q10:
        raise ValueError("Aucune formule retenue n'a fourni de Q10.")

    q10_moy = sum(valeurs_q10) / len(valeurs_q10)

    if verbose:
        print("\n── Estimation Q10 (Gradex) ──")
        for nom, q in zip(formules_retenues, valeurs_q10):
            print(f"  {nom:<25} Q10 = {q:>10.3f} m³/s")
        print(f"  {'Moyenne retenue':<25} Q10 = {q10_moy:>10.3f} m³/s")

    return q10_moy


# =============================================================================
# 7. MÉTHODE DU GRADEX
# =============================================================================

def _gumbel_variate(T: float) -> float:
    """Variable réduite de Gumbel : u_T = −ln(−ln(1 − 1/T))"""
    return -math.log(-math.log(1.0 - 1.0 / T))


def gradex_debits_24h(
    gradex_pluie: float,
    S_km2: float,
    Tc_h: float
) -> float:
    # Formule calée sur les données du projet (facteur 86.4 = 3.6×24)
    return gradex_pluie * (Tc_h / 24)**0.3


def gradex_debits_pointe(
    gradex_pluie: float,
    S_km2: float,
    Tc_h: float
) -> float:
    
    return gradex_debits_24h(gradex_pluie, S_km2, Tc_h) * S_km2/(3.6*Tc_h)


def methode_gradex(
    Q10_ref: float,
    gradex_pluie: float,
    S_km2: float,
    Tc_h: float,
    periodes: List[int] = None,
    verbose: bool = True
) -> Dict[int, float]:
    if periodes is None:
        periodes = [10, 20, 50, 100, 1000]

    Gq_24h   = gradex_debits_24h(gradex_pluie, S_km2, Tc_h)
    Gq_pointe = Gq_24h * S_km2/(3.6*Tc_h)

    u10 = _gumbel_variate(10)

    resultats = {}
    for T in periodes:
        u_T = _gumbel_variate(T)
        Q_T = Q10_ref + Gq_pointe * (u_T - u10)
        resultats[T] = Q_T

    if verbose:
        print("\n── Méthode du Gradex ──")
        print(f"  Gradex pluie       = {gradex_pluie:.4f} mm")
        print(f"  Tc                 = {Tc_h:.4f} h  ({Tc_h*60:.2f} min)")
        print(f"  Gq (24h)           = {Gq_24h:.4f} m³/s")
        print(f"  Gq (pointe)        = {Gq_pointe:.4f} m³/s")
        print(f"  Q10 (référence)    = {Q10_ref:.4f} m³/s")
        print(f"\n  {'T (ans)':<12} {'u_T':>8}  {'Q_T (m³/s)':>14}")
        print(f"  {'-'*38}")
        for T, Q in resultats.items():
            print(f"  {T:<12} {_gumbel_variate(T):>8.4f}  {Q:>14.3f}")

    return resultats


# =============================================================================
# 8. RÉSULTATS FINAUX — Q50, Q100 et MOYENNE TOUTES FORMULES
# =============================================================================

def resultats_finaux(
    debits_par_formule: Dict[str, Dict[int, float]],
    debits_gradex: Dict[int, float],
    formules_exclues: Optional[List[str]] = None,
    periodes_cibles: List[int] = None,
    verbose: bool = True
) -> Dict[int, float]:
    """
    Calcule la valeur retenue pour Q50 et Q100 comme moyenne de toutes les
    formules (Rationnelle, Mac-Math, Fuller II, Mallet-Gauthier,
    Hazen-Lazervic, Francou-Rodier et méthode du Gradex).

    Paramètres
    ----------
    debits_par_formule : {nom: {T: Q}} — résultats des formules empiriques
    debits_gradex      : {T: Q} — résultats de la méthode du Gradex
    formules_exclues   : formules à exclure de la moyenne (ex. ['Fuller II'])
    periodes_cibles    : [50, 100] par défaut

    Retourne
    --------
    {T: Q_moyen_retenu_m3s}
    """
    if periodes_cibles is None:
        periodes_cibles = [50, 100]
    if formules_exclues is None:
        formules_exclues = []

    # Ajouter la méthode du Gradex dans l'ensemble
    tous_debits = dict(debits_par_formule)
    tous_debits["Gradex"] = debits_gradex

    resultats_moyens = {}
    for T in periodes_cibles:
        valeurs = []
        for nom, qdict in tous_debits.items():
            if nom in formules_exclues:
                continue
            if T in qdict:
                valeurs.append((nom, qdict[T]))

        if not valeurs:
            resultats_moyens[T] = float("nan")
            continue

        q_moyen = sum(v for _, v in valeurs) / len(valeurs)
        resultats_moyens[T] = q_moyen

        if verbose:
            print(f"\n── Résultats Q{T} ──")
            print(f"  {'Formule':<25} {'Q_{}'.format(T):>12}")
            print(f"  {'-'*40}")
            for nom, q in valeurs:
                print(f"  {nom:<25} {q:>12.3f} m³/s")
            print(f"  {'Valeur retenue (moy.)':<25} {q_moyen:>12.3f} m³/s")

    return resultats_moyens


# =============================================================================
# 9. CALCUL COMPLET — FONCTION DE SYNTHÈSE
# =============================================================================

def calcul_complet(
    bv: BassinVersant,
    station_pluvio: StationPluviometrique,
    station_hydro: StationHydrometrique,
    # Paramètres Montana
    a_montana: List[float],           # [a10, a20, a50, a100] en mm/min
    b_montana: List[float],           # [b10, b20, b50, b100]
    # Paramètres formules débit
    C_rationnel: float = 0.42,        # coefficient de ruissellement
    K_macmath: float = 0.48,          # coeff. Mac-Math
    A_fuller: float = 3.2,            # coeff. Fuller (oueds sahariens ≈ 3.2)
    N_fuller: float = 80,             # coeff. Fuller
    k_mg: float = 5.5,                # coeff. k Mallet-Gautier
    a_mg: float = 20,              # coeff. a Mallet-Gautier (calibration régionale)
    K1_hl: float = 13.47,             # coeff. Hazen-Lazervic K1
    K2_hl: float = 0.587,             # coeff. Hazen-Lazervic K2
    a_hl: float = 0.8,                # exposant Hazen-Lazervic
    # Sélection des formules Tc
    formules_tc: Optional[List[str]] = None,
    # Formules Q à exclure de la moyenne finale
    formules_exclues_finale: Optional[List[str]] = None,
    periodes: List[int] = None,
    verbose: bool = True
) -> Dict:
    """
    Calcul hydrologique complet selon la méthodologie de la note de calcul.

    Retourne un dictionnaire synthèse avec tous les résultats.
    """
    if periodes is None:
        periodes = [10, 20, 50, 100]

    if verbose:
        print("=" * 65)
        print(f"  CALCUL HYDROLOGIQUE — {bv.nom}")
        print("=" * 65)
        print(bv.resume())

    # ── (A) Temps de concentration ──────────────────────────────────────────
    tc_resultats = calculer_tc_bv(bv, formules_tc, verbose=verbose)
    Tc_moy_min = tc_resultats["Moyenne"]
    Tc_moy_h   = Tc_moy_min / 60.0

    # ── (B) Intensités Montana ───────────────────────────────────────────────
    intensites = intensites_montana(a_montana, b_montana, Tc_moy_min, periodes)
    if verbose:
        print(f"\n── Intensités Montana (Tc={Tc_moy_min:.2f} min) ──")
        for T, i in intensites.items():
            print(f"  i(T={T:<4d}) = {i:.5f} mm/h  "
                  f"({i/60:.5f} mm/min)")

    # ── (C) Pluies Pj24h ────────────────────────────────────────────────────
    pj24h = {T: station_pluvio.pj24h[T] for T in periodes if T in station_pluvio.pj24h}
    if verbose:
        print(f"\n── Pluies Pj24h (station '{station_pluvio.nom}') ──")
        for T, pj in pj24h.items():
            print(f"  Pj(T={T:<4d}) = {pj:.1f} mm")

    # ── (D) Débits de pointe ─────────────────────────────────────────────────
    debits = {}

    # Rationnelle
    debits["Rationnelle"] = debits_rationnels(C_rationnel, intensites, bv.superficie)

    # Mac-Math
    debits["Mac-Math"] = debits_macmath(K_macmath, bv.superficie, bv.pente(), pj24h)

    # Fuller II
    debits["Fuller II"] = debits_fuller2(A_fuller, N_fuller, bv.superficie, periodes)

    # Mallet-Gautier
    debits["Mallet-Gauthier"] = debits_mallet_gauthier(
        k_mg, a_mg, station_pluvio.hauteur_annuelle,
        bv.superficie, bv.longueur, periodes
    )

    # Hazen-Lazervic (avec Pj_1000 estimé par Gumbel)
    debits["Hazen-Lazervic"] = debits_hazen_lazervic(
        K1_hl, K2_hl,
        bv.superficie,
        pj24h_10=pj24h.get(10, list(pj24h.values())[0]),
        gradex_pluie=station_pluvio.gradex,
        a_exp=a_hl,
        periodes=periodes
    )

    # Francou-Rodier
    debits["Francou-Rodier"] = debits_francou_rodier(
        station_hydro, bv.superficie, periodes
    )

    if verbose:
        print("\n── Débits de pointe par formule (m³/s) ──")
        header = f"  {'Formule':<22}" + "".join(f"  Q{T:<5}" for T in periodes)
        print(header)
        print(f"  {'-'*(22 + 9*len(periodes))}")
        for nom, qdict in debits.items():
            ligne = f"  {nom:<22}" + "".join(f"  {qdict.get(T, float('nan')):>7.2f}" for T in periodes)
            print(ligne)

    # ── (E) Estimation Q10 Gradex ────────────────────────────────────────────
    # Exclure Fuller II de la moyenne Q10 (valeurs hors-échelle)
    Q10_ref = estimer_q10_gradex(
        debits,
        formules_retenues=[k for k in debits if "fuller" not in k.lower()],
        verbose=verbose
    )

    # ── (F) Méthode du Gradex ────────────────────────────────────────────────
    debits_gradex = methode_gradex(
        Q10_ref,
        station_pluvio.gradex,
        bv.superficie,
        Tc_moy_h,
        periodes=[10, 20, 50, 100, 1000],
        verbose=verbose
    )

    # ── (G) Résultats finaux Q50, Q100 ──────────────────────────────────────
    if formules_exclues_finale is None:
        formules_exclues_finale = ["Fuller II"]

    q_finaux = resultats_finaux(
        debits,
        debits_gradex,
        formules_exclues=formules_exclues_finale,
        periodes_cibles=[50, 100],
        verbose=verbose
    )

    if verbose:
        print("\n" + "=" * 65)
        print("  RÉSUMÉ FINAL")
        print("=" * 65)
        for T, Q in q_finaux.items():
            print(f"  Q{T:<4d} retenu = {Q:.3f} m³/s")
        Q_gradex_100 = debits_gradex.get(100, float("nan"))
        Q_gradex_50  = debits_gradex.get(50,  float("nan"))
        print(f"\n  Q100 (Gradex seul) = {Q_gradex_100:.3f} m³/s")
        print(f"  Q50  (Gradex seul) = {Q_gradex_50:.3f} m³/s")
        print("=" * 65)

    return {
        "bv": bv,
        "tc": tc_resultats,
        "Tc_min": Tc_moy_min,
        "Tc_h": Tc_moy_h,
        "intensites": intensites,
        "pj24h": pj24h,
        "debits": debits,
        "Q10_gradex": Q10_ref,
        "debits_gradex": debits_gradex,
        "q_finaux": q_finaux,
    }


# =============================================================================
# 10. EXEMPLE D'APPLICATION — BASSIN VERSANT BERTATE
# =============================================================================

if __name__ == "__main__":

    # ── Stations pluviométriques ─────────────────────────────────────────────
    station_barrage = StationPluviometrique(
        nom="Station Ansegmir ",
        x=545690, y=238723,
        annees=list(range(1960, 2024)),
        pluie=[26.6, 19.4, 31.2, 31.4, 36.0, 32.6, 12.1, 21.9, 55.3, 29.4,
               16.5, 21.2, 30.0, 23.2, 16.7, 19.3, 20.7, 17.7, 16.6, 24.8,
               23.5, 8.4, 79.5, 18.9, 10.5, 35.4, 14.8, 26.2, 31.2, 24.8,
               21.4, 25.5, 21.0, 60.4, 10.8, 22.0, 37.7, 33.1, 21.0, 16.7,
               42.4, 23.0, 32.5, 27.9, 26.0, 25.2, 39.7, 24.5, 41.8, 28.6,
               24.2, 24.9, 18.7, 16.6, 20.9, 100.2, 28.1, 14.0, 29.5, 11.5,
               11.7, 17.0, 30.0, 29.2],
        pj24h={10: 43.4, 20: 51.2, 50: 61.6, 100: 69.7},
        gradex=11.75,
        hauteur_annuelle=27.09
    )

    station_midelt = StationPluviometrique(
        nom="Barrage Hassan II Midelt",
        x=577600, y=248500,
        annees=list(range(2001, 2024)),
        pluie=[24.8, 9.0, 23.8, 25.6, 32.2, 21.3, 25.5, 39.0, 50.2, 17.0,
               24.8, 27.8, 25.9, 14.1, 59.2, 19.0, 20.3, 27.2, 12.5, 12.4,
               31.9, 27.4, 20.2],
        pj24h={10: 41.1, 20: 48.1, 50: 57.5, 100: 64.7},
        gradex=9.04,
        hauteur_annuelle=25.70
    )

    station_zaida_pluie = StationPluviometrique(
        nom="Station Midelt Délégation",
        x=561800, y=231200,
        annees=list(range(1977, 2024)),
        pluie=[17.2, 26.4, 28.6, 12.8, 17.3, 26.5, 16.8, 9.7, 26.0, 16.5,
               19.3, 25.3, 32.2, 13.9, 19.6, 26.3, 40.5, 30.0, 25.0, 87.7,
               52.3, 58.0, 46.8, 22.3, 30.9, 15.6, 33.0, 27.5, 43.5, 16.6,
               30.7, 25.4, 12.0, 27.8, 15.0, 36.0, 18.4, 18.0, 49.8, 12.5,
               19.5, 16.2, 21.1, 19.0, 23.8, 28.0],
        pj24h={10: 42.7, 20: 50.4, 50: 60.6, 100: 68.6},
        gradex=11.16,
        hauteur_annuelle=26.64
    )

    station_ansegmir = StationPluviometrique(
        nom="Station Zaida (pluie)",
        x=541100, y=247000,
        annees=list(range(1964, 2023)),
        pluie=[29.3, 25.5, 19.2, 16.6, 28.4, 15.6, 28.6, 22.3, 21.5, 23.9,
               44.9, 90.9, 13.3, 17.2, 28.0, 18.9, 24.1, 16.1, 55.6, 12.2,
               45.6, 16.0, 16.9, 49.2, 29.2, 18.0, 24.0, 30.0, 13.2, 26.3,
               24.2, 28.7, 23.8, 39.2, 26.3, 20.5, 19.5, 48.4, 17.0, 17.2,
               35.0, 29.2, 14.3, 19.2, 46.3, 18.8, 21.2, 24.9, 28.0, 17.0,
               23.0, 19.2, 23.0, 22.2, 16.9, 49.2, 29.2, 18.0, 24.0],
        pj24h={10: 39.9, 20: 46.1, 50: 54.4, 100: 60.8},
        gradex=10.17,
        hauteur_annuelle=25.98
    )

    # ── Station hydrométrique ────────────────────────────────────────────────
    station_zaida_hydro = StationHydrometrique(
        nom="Station Zaida (débit)",
        x=541100, y=247000,
        annees=list(range(1959, 2021)),
        debit=[18.7, 78.9, 8.32, 54.9, 141.0, 39.7, 25.3, 7.36, 4.03, 78.2,
               113.0, 131.0, 58.9, 39.4, 20.8, 34.1, 41.5, 52.8, 84.1, 55.5,
               125.0, 30.6, 4.49, 20.2, 12.3, 10.4, 10.9, 30.6, 56.4, 47.2,
               47.4, 26.8, 26.6, 84.7, 57.9, 33.4, 12.2, 145.0, 54.8, 51.0,
               25.7, 70.3, 11.9, 58.1, 185.0, 37.7, 10.3, 87.3, 3.56, 75.3,
               76.8, 269.0, 26.4, 120.0, 101.0, 22.5, 38.2, 15.1, 12.4, 148.0,
               6.11, 9.97],
        superficie_jaugee=102.0,
        qj={10: 121.0, 20: 155.0, 50: 200.0, 100: 233.0}
    )

    # ── Bassin versant Bertate ───────────────────────────────────────────────
    bv_bertate = BassinVersant(
        nom="Bertate",
        x_exutoire=598988.451,
        y_exutoire=228875.64,
        superficie=100,      # km²
        perimetre=45.016,       # km
        zmin=1503,              # m NGM
        zmax=2318,              # m NGM
        z95=None,               # non disponible pour ce BV
        z5=None,
        longueur=17.047         # km
    )

    # ── Coefficients Montana (station Errachidia) ────────────────────────────
    # a en mm/min, b sans unité — pour T=10, 20, 50, 100
    a_montana = [7.45, 8.10, 10.20, 12.40]
    b_montana = [0.49, 0.50, 0.51,  0.53]

    # ── Calcul complet ───────────────────────────────────────────────────────
    liste_stations_pluvio = [
        station_barrage, station_midelt, station_zaida_pluie, station_ansegmir
    ]

    # Sélection des stations de référence
    print("\n── Sélection des stations de référence ──")
    st_pluvio = station_referencePJ(bv_bertate, liste_stations_pluvio, ["plus proche"])
    st_hydro  = station_referenceQJ(bv_bertate, [station_zaida_hydro], ["plus proche"])

    resultats = calcul_complet(
        bv=bv_bertate,
        station_pluvio=st_pluvio,
        station_hydro=st_hydro,
        a_montana=a_montana,
        b_montana=b_montana,
        C_rationnel=0.42,
        K_macmath=0.48,
        A_fuller=3.2,
        N_fuller=80,
        k_mg=5.5,
        a_mg=20,
        K1_hl=13.47,
        K2_hl=0.587,
        a_hl=0.8,
        formules_tc=None,         # toutes les formules
        formules_exclues_finale=["Fuller II"],
        verbose=True
    )
