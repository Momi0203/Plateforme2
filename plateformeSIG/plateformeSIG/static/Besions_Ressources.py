"""Calcul des besoins en eau et bilan des ressources.

Calendrier utilise: Septembre -> Aout (12 mois).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Protocol

import pandas as pd

from bilan1 import ressource_crue


MOIS_SEP_AOU = ["Sep", "Oct", "Nov", "Dec", "Jan", "Fev", "Mar", "Avr", "Mai", "Jui", "Jul", "Aou"]
JOURS_MOIS_STD = [30, 31, 30, 31, 31, 29, 31, 30, 31, 30, 31, 31]

# Table simplifiee de Ra (mm/j), indexee par latitude.
RA_TABLE = {
    20.0: [13.5, 12.0, 10.5, 9.8, 10.2, 11.5, 13.2, 14.8, 15.8, 16.2, 15.9, 15.0],
    25.0: [13.6, 11.9, 10.2, 9.4, 9.8, 11.2, 13.0, 14.8, 16.0, 16.5, 16.2, 15.2],
    30.0: [13.7, 11.8, 10.0, 9.0, 9.3, 10.8, 12.8, 14.7, 16.1, 16.8, 16.5, 15.4],
    32.0: [13.7, 11.7, 9.8, 8.8, 9.1, 10.6, 12.6, 14.6, 16.1, 16.9, 16.6, 15.5],
    34.0: [13.8, 11.6, 9.7, 8.6, 8.9, 10.4, 12.5, 14.5, 16.1, 17.0, 16.7, 15.6],
    35.0: [13.8, 11.5, 9.6, 8.5, 8.8, 10.3, 12.4, 14.5, 16.1, 17.1, 16.8, 15.6],
    40.0: [13.9, 11.3, 9.2, 8.0, 8.2, 9.8, 12.0, 14.2, 16.0, 17.2, 16.9, 15.8],
}


def _check_12(nom: str, valeurs: List[float]) -> None:
    if len(valeurs) != 12:
        raise ValueError(f"{nom} doit contenir 12 valeurs.")


def _interp_latitude(table: dict[float, List[float]], latitude: float, mois_index: int) -> float:
    lats = sorted(table.keys())
    if latitude <= lats[0]:
        return table[lats[0]][mois_index]
    if latitude >= lats[-1]:
        return table[lats[-1]][mois_index]
    for i in range(len(lats) - 1):
        lo = lats[i]
        hi = lats[i + 1]
        if lo <= latitude <= hi:
            t = (latitude - lo) / (hi - lo)
            return table[lo][mois_index] + t * (table[hi][mois_index] - table[lo][mois_index])
    return table[lats[0]][mois_index]


def _sep_aou_to_jan_dec(v: List[float]) -> List[float]:
    """[Sep..Aou] -> [Jan..Dec]."""
    return [v[4], v[5], v[6], v[7], v[8], v[9], v[10], v[11], v[0], v[1], v[2], v[3]]


def _jan_dec_to_sep_aou(v: List[float]) -> List[float]:
    """[Jan..Dec] -> [Sep..Aou]."""
    return [v[8], v[9], v[10], v[11], v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7]]


@dataclass
class StationClimatique:
    nom: str
    latitude: float
    temperatures_moyennes: List[float]  # deg C, Sep->Aou
    taux_insolation: List[float]  # n/N, Sep->Aou
    precipitations_moyennes: List[float]  # mm/mois, Sep->Aou
    jours_mois: List[int] = None

    def __post_init__(self) -> None:
        _check_12("temperatures_moyennes", self.temperatures_moyennes)
        _check_12("taux_insolation", self.taux_insolation)
        _check_12("precipitations_moyennes", self.precipitations_moyennes)
        self.jours_mois = self.jours_mois[:] if self.jours_mois else JOURS_MOIS_STD[:]
        _check_12("jours_mois", self.jours_mois)

    def ra_mm_j(self, mois: int) -> float:
        return _interp_latitude(RA_TABLE, self.latitude, mois)

    def kt(self, mois: int) -> float:
        # Hargreaves simplifie avec DeltaT estime via n/N.
        n_n = self.taux_insolation[mois]
        t_moy = self.temperatures_moyennes[mois]
        delta_t =  t_moy
        return 0.031 * math.sqrt(max(delta_t, 0.0))+0.24 

    def eto_mm_j(self, mois: int) -> float:
        n_n = self.taux_insolation[mois]
        t_moy = self.temperatures_moyennes[mois]
        kt=0.031 * math.sqrt(max(t_moy, 0.0))+0.24 
        return n_n*kt *(0.457*t_moy+8.13)

    def eto_mm_mois(self, mois: int) -> float:
        return self.eto_mm_j(mois) * self.jours_mois[mois]

    def pluie_efficace_mm_mois(self, mois: int) -> float:
        p = self.precipitations_moyennes[mois]
        if p < 75:
            return 0.60 * p
        else :return 0.80 * p

    #def pluie_efficace_mm_j(self, mois: int) -> float:
        #return self.pluie_efficace_mm_mois(mois) 

    def tableau(self) -> pd.DataFrame:
        rows = []
        for i in range(12):
            rows.append(
                {
                    "Mois": MOIS_SEP_AOU[i],
                    "T_moy (C)": round(self.temperatures_moyennes[i], 1),
                    "n/N": round(self.taux_insolation[i], 2),
                    "P (mm/mois)": round(self.precipitations_moyennes[i], 1),
                    "Kt": round(self.kt(i), 4),
                    "ETo (mm/j)": round(self.eto_mm_j(i), 2),
                    "ETo (mm/mois)": round(self.eto_mm_mois(i), 1),
                    "Pluie eff. (mm/mois)": round(self.pluie_efficace_mm_mois(i), 1),
                }
            )
        return pd.DataFrame(rows)


@dataclass
class Culture:
    nom: str
    kc: List[float]  # 12 valeurs
    kr: List[float]  # 12 valeurs
    superficie_ha: float
    efficacite_reseau: float = 0.9   # on prend 0.9 mais on va lie une models perimetre quand calcul par une apps efficiance de reseaux 

    def __post_init__(self) -> None:
        _check_12("kc", self.kc)
        _check_12("kr", self.kr)
        if self.superficie_ha < 0:
            raise ValueError("superficie_ha doit etre positive.")
        if not (0 < self.efficacite_reseau <= 1.0):
            raise ValueError("efficacite_reseau doit etre entre 0 et 1.")

    def etc_mm_j(self, station: StationClimatique, mois: int) -> float:
        return station.eto_mm_j(mois) * self.kc[mois]* self.kr[mois]


    def besoins_bruts_mm_j(self, station: StationClimatique, mois: int) -> float:
        return self.etc_mm_j(station, mois) / self.efficacite_reseau
    
    def besoins_reel_mm_j(self, station: StationClimatique, mois: int) -> float:
        brut = self.besoins_bruts_mm_j(station, mois) - station.pluie_efficace_mm_mois(mois)
        return max(0.0, brut)
    
    def besoins_bruts_m3_j(self, station: StationClimatique, mois: int) -> float:
        # 1 mm sur 1 ha = 10 m3.
        return self.besoins_bruts_mm_j(station, mois) * self.superficie_ha * 10.0
    
    def besoins_reel_m3_j(self, station: StationClimatique, mois: int) -> float:
        # 1 mm sur 1 ha = 10 m3.
        return self.besoins_reel_mm_j(station, mois) * self.superficie_ha * 10.0

    def besoins_bruts_m3_mois(self, station: StationClimatique, mois: int) -> float:
        return self.besoins_bruts_m3_j(station, mois) * station.jours_mois[mois]
    
    def besoins_reel_m3_mois(self, station: StationClimatique, mois: int) -> float:
        return self.besoins_reel_m3_j(station, mois) * station.jours_mois[mois]
    
    def tableau(self, station: StationClimatique) -> pd.DataFrame:
        rows = []
        for i in range(12):
            rows.append(
                {
                    "Mois": MOIS_SEP_AOU[i],
                    "Kc": self.kc[i],
                    "Kr": self.kr[i],
                    "ETc (mm/j)": round(self.etc_mm_j(station, i), 2),
                    "Besoin reel (mm/j)": round(self.besoins_reel_mm_j(station, i), 2),
                    "Besoins bruts (mm/j)": round(self.besoins_bruts_mm_j(station, i), 2),
                    "Besoins reel (m3/j)": round(self.besoins_reel_m3_j(station, i), 1),
                    "Besoins reel (m3/mois)": round(self.besoins_reel_m3_mois(station, i), 0),
                }
            )
        return pd.DataFrame(rows)


@dataclass
class BassinVersant:
    nom: str
    superficie_km2: float


@dataclass
class StationHydrometrique:
    nom: str
    debits_mensuels_m3s_sep_aou: List[float]
    superficie_bv_jaugee_km2: float

    def __post_init__(self) -> None:
        _check_12("debits_mensuels_m3s_sep_aou", self.debits_mensuels_m3s_sep_aou)


class Ressource(Protocol):
    nom: str

    def calculer_apport_mensuel(self, jours_mois: List[int] | None = None, annee_humide: bool = False) -> List[float]:
        ...


@dataclass
class Crues:
    bassin: BassinVersant
    station: StationHydrometrique
    tc_h: float
    b: float # les dimensions de canal principal lie a Perimetre 
    y: float
    z: float
    pente: float
    manning_n: float
    coeff_humide: float = 1.30

    def __post_init__(self) -> None:
        self.nom = f"Crues ({self.bassin.nom})"
        self._cache_normale: List[float] | None = None

    def _apport_normal_sep_aou(self) -> List[float]:
        if self._cache_normale is None:
            debits_jan_dec = _sep_aou_to_jan_dec(self.station.debits_mensuels_m3s_sep_aou)
            volumes_jan_dec = ressource_crue(
                self.tc_h,
                self.b,
                self.y,
                self.z,
                self.pente,
                self.manning_n,
                debits_jan_dec,
                self.bassin.superficie_km2,
                self.station.superficie_bv_jaugee_km2,
            )
            self._cache_normale = _jan_dec_to_sep_aou(volumes_jan_dec)
        return self._cache_normale

    def calculer_apport_mensuel(self, jours_mois: List[int] | None = None, annee_humide: bool = False) -> List[float]:
        base = self._apport_normal_sep_aou()
        facteur = self.coeff_humide if annee_humide else 1.0
        return [v * facteur for v in base]


@dataclass
class Puits:
    nom: str
    debit_moyen_m3_h: float
    duree_pompage_h_j: float

    def apport_journalier_m3(self) -> float:
        return self.debit_moyen_m3_h * self.duree_pompage_h_j

    def calculer_apport_mensuel(self, jours_mois: List[int] | None = None, annee_humide: bool = False) -> List[float]:
        jours = jours_mois[:] if jours_mois else JOURS_MOIS_STD[:]
        _check_12("jours_mois", jours)
        return [self.apport_journalier_m3() * j for j in jours]


@dataclass
class Khettara:
    nom: str
    debit_m3_j: List[float]
    debit_humide_m3_j: List[float]

    def __post_init__(self) -> None:
        _check_12("debit_m3_j", self.debit_m3_j)
        _check_12("debit_humide_m3_j", self.debit_humide_m3_j)

    def calculer_apport_mensuel(self, jours_mois: List[int] | None = None, annee_humide: bool = False) -> List[float]:
        jours = jours_mois[:] if jours_mois else JOURS_MOIS_STD[:]
        _check_12("jours_mois", jours)
        debits = self.debit_humide_m3_j if annee_humide else self.debit_m3_j
        return [q * j for q, j in zip(debits, jours)]


@dataclass
class Source:
    nom: str
    debit_m3_j: List[float]
    debit_humide_m3_j: List[float]

    def __post_init__(self) -> None:
        _check_12("debit_m3_j", self.debit_m3_j)
        _check_12("debit_humide_m3_j", self.debit_humide_m3_j)

    def calculer_apport_mensuel(self, jours_mois: List[int] | None = None, annee_humide: bool = False) -> List[float]:
        jours = jours_mois[:] if jours_mois else JOURS_MOIS_STD[:]
        _check_12("jours_mois", jours)
        debits = self.debit_humide_m3_j if annee_humide else self.debit_m3_j
        return [q * j for q, j in zip(debits, jours)]


@dataclass
class Barrage:
    nom: str
    lachers_m3_mois: List[float]
    lachers_humide_m3_mois: List[float]

    def __post_init__(self) -> None:
        _check_12("lachers_m3_mois", self.lachers_m3_mois)
        _check_12("lachers_humide_m3_mois", self.lachers_humide_m3_mois)

    def calculer_apport_mensuel(self, jours_mois: List[int] | None = None, annee_humide: bool = False) -> List[float]:
        return self.lachers_humide_m3_mois[:] if annee_humide else self.lachers_m3_mois[:]


@dataclass
class AutreSource:
    nom: str
    debit_m3_j: List[float]
    debit_humide_m3_j: List[float]

    def __post_init__(self) -> None:
        _check_12("debit_m3_j", self.debit_m3_j)
        _check_12("debit_humide_m3_j", self.debit_humide_m3_j)

    def calculer_apport_mensuel(self, jours_mois: List[int] | None = None, annee_humide: bool = False) -> List[float]:
        jours = jours_mois[:] if jours_mois else JOURS_MOIS_STD[:]
        _check_12("jours_mois", jours)
        debits = self.debit_humide_m3_j if annee_humide else self.debit_m3_j
        return [q * j for q, j in zip(debits, jours)]


def bilan_general(
    cultures: List[Culture],
    ressources: List[Ressource],
    station_climatique: StationClimatique,
    annee_humide: bool = False,
) -> pd.DataFrame:
    jours = station_climatique.jours_mois

    besoins_m3_mois = [
        sum(c.besoins_bruts_m3_mois(station_climatique, i) for c in cultures) for i in range(12)
    ]

    ressources_m3_mois = [0.0] * 12
    for res in ressources:
        apports = res.calculer_apport_mensuel(jours_mois=jours, annee_humide=annee_humide)
        _check_12(f"apports {res.nom}", apports)
        for i in range(12):
            ressources_m3_mois[i] += apports[i]

    bilan_m3 = [r - b for r, b in zip(ressources_m3_mois, besoins_m3_mois)]
    deficit_m3 = [max(0.0, -x) for x in bilan_m3]
    excedent_m3 = [max(0.0, x) for x in bilan_m3]

    rows = []
    for i in range(12):
        rows.append(
            {
                "Mois": MOIS_SEP_AOU[i],
                "Besoins (m3/mois)": round(besoins_m3_mois[i], 0),
                "Ressources (m3/mois)": round(ressources_m3_mois[i], 0),
                "Bilan (m3/mois)": round(bilan_m3[i], 0),
                "Deficit (m3/mois)": round(deficit_m3[i], 0),
                "Excedent (m3/mois)": round(excedent_m3[i], 0),
            }
        )

    rows.append(
        {
            "Mois": "TOTAL",
            "Besoins (m3/mois)": round(sum(besoins_m3_mois), 0),
            "Ressources (m3/mois)": round(sum(ressources_m3_mois), 0),
            "Bilan (m3/mois)": round(sum(bilan_m3), 0),
            "Deficit (m3/mois)": round(sum(deficit_m3), 0),
            "Excedent (m3/mois)": round(sum(excedent_m3), 0),
        }
    )
    return pd.DataFrame(rows)


def main() -> None:
    # 1) Station climatique
    station_clim = StationClimatique(
        nom="Agadir",
        latitude=30.4,
        temperatures_moyennes=[25.8, 23.5, 19.2, 15.6, 13.4, 14.0, 16.7, 18.0, 21.6, 24.7, 27.8, 28.5],
        taux_insolation=[0.72, 0.70, 0.68, 0.65, 0.63, 0.65, 0.70, 0.75, 0.78, 0.82, 0.85, 0.80],
        precipitations_moyennes=[8.3, 26.1, 43.7, 54.6, 56.5, 63.0, 74.7, 65.4, 41.4, 6.8, 0.9, 0.5],
    )

    # 2) Cultures
    agrumes = Culture(nom="Agrumes", kc=[0.70] * 12, kr=[0.65] * 12, superficie_ha=25.97, efficacite_reseau=0.85)
    maraichage = Culture(
        nom="Maraichage",
        kc=[0.60, 0.75, 0.90, 1.05, 1.10, 1.05, 0.95, 0.85, 0.75, 0.65, 0.55, 0.55],
        kr=[0.80] * 12,
        superficie_ha=10.0,
        efficacite_reseau=0.85,
    )
    cultures = [agrumes, maraichage]

    # 3) Ressources (6 types)
    bassin = BassinVersant("Oued Souss", superficie_km2=50.0)
    station_hydro = StationHydrometrique(
        nom="Aoulouz",
        debits_mensuels_m3s_sep_aou=[4.5, 6.2, 9.4, 5.8, 3.8, 2.1, 1.2, 0.8, 1.5, 6.2, 9.4, 5.8],
        superficie_bv_jaugee_km2=80.0,
    )
    crues = Crues(bassin=bassin, station=station_hydro, tc_h=1.5, b=0.6, y=0.6, z=1.0, pente=0.001, manning_n=0.015)

    puits = Puits(nom="Puits P1", debit_moyen_m3_h=15.0, duree_pompage_h_j=8.0)
    khettara = Khettara(
        nom="Khettara K1",
        debit_m3_j=[120, 115, 110, 105, 100, 100, 105, 110, 115, 120, 125, 125],
        debit_humide_m3_j=[150, 145, 140, 135, 130, 130, 135, 140, 145, 150, 155, 155],
    )
    source = Source(
        nom="Source Atlas",
        debit_m3_j=[80, 85, 90, 95, 90, 85, 80, 75, 70, 75, 80, 80],
        debit_humide_m3_j=[100, 105, 110, 115, 110, 105, 100, 95, 90, 95, 100, 100],
    )
    barrage = Barrage(
        nom="Barrage YBT",
        lachers_m3_mois=[5000, 8000, 10000, 12000, 10000, 8000, 6000, 4000, 2000, 1000, 500, 3000],
        lachers_humide_m3_mois=[6500, 10400, 13000, 15600, 13000, 10400, 7800, 5200, 2600, 1300, 650, 3900],
    )
    autre = AutreSource(
        nom="Retenue collinaire",
        debit_m3_j=[50, 60, 70, 80, 70, 60, 50, 40, 30, 20, 10, 30],
        debit_humide_m3_j=[65, 78, 91, 104, 91, 78, 65, 52, 39, 26, 13, 39],
    )

    ressources: List[Ressource] = [crues, puits, khettara, source, barrage, autre]

    print("=== DONNEES CLIMATIQUES ===")
    print(station_clim.tableau().to_string(index=False))

    for culture in cultures:
        print(f"\n=== BESOINS CULTURE: {culture.nom} ===")
        print(culture.tableau(station_clim).to_string(index=False))

    print("\n=== BILAN GENERAL (ANNEE NORMALE) ===")
    print(bilan_general(cultures, ressources, station_clim, annee_humide=False).to_string(index=False))

    print("\n=== BILAN GENERAL (ANNEE HUMIDE) ===")
    print(bilan_general(cultures, ressources, station_clim, annee_humide=True).to_string(index=False))


if __name__ == "__main__":
    main()
