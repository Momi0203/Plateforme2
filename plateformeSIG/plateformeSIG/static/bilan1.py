import math
import numpy as np
import matplotlib.pyplot as plt
# ── 5.6 Formule de Francou-Rodier (UFR) ──────────────────────────────────────
def debits_francou_rodier(
    station_hydro, #StationHydrometrique
    S_km2, #  float 
    S_jauge_km2 #StationHydrometrique surface de bv jauge,
):
    periodes=["Jan", "Fev", "Mar", "Avr", "Mai", "Jui",
                  "Jul", "Aou", "Sep", "Oct", "Nov", "Dec"] 
    S_bv_km2    = S_km2  
    log_S_jauge = math.log10(S_jauge_km2)
    resultats = []
    for Q in station_hydro:
        k_T = 10.0 * (1.0 - (math.log10(Q) - 6.0) / (log_S_jauge - 8.0))
        Q_T = 1e6 * (S_bv_km2 / 1e8) ** (1.0 - k_T / 10.0)
        resultats.append(Q_T)
    return resultats
def manning_debit(A, P, S, n):
    """
    Calcule le débit avec la formule de Manning
    
    A : aire mouillée (m²)
    P : périmètre mouillé (m)
    S : pente (m/m)
    n : coefficient de Manning
    """
    if P == 0 or n == 0:
        return 0
    
    R = A / P  # rayon hydraulique
    
    Q = (1/n) * A * (R ** (2/3)) * math.sqrt(S)
    
    return Q
def canal_trapezoidal(b, y, z, S, n):
    """
    b : largeur de fond (m)
    y : hauteur d'eau (m)
    z : talus (horizontal/vertical)
    """
    A = (b + z*y) * y
    P = b + 2*y*math.sqrt(1 + z**2)
    
    return manning_debit(A, P, S, n)
def hydrogramme_crue(t, Tc, Qp, Qdmax):
    if Tc == 0:
        return 0
    
    try:
        # Formule hydrogramme (type gamma / Nash simplifié)
        Q = Qp * (t/Tc) ** 4 * math.exp(4 - 4*(t/Tc))
        
        # Écrêtement (débit max limité)
        return min(Q, Qdmax)
    
    except OverflowError:
        return 0
def integrale_trapeze(f, a, b, n):
    """Calcule l'intégrale par la méthode des trapèzes."""
    h = (b - a) / n
    somme = (f(a) + f(b)) / 2.0
    for i in range(1, n):
        x = a + i * h
        somme += f(x)
    return somme * h
def ressource_crue(Tc, b, y, z, S, n, station_hydro, S_km2, S_jauge_km2):
        Qi = debits_francou_rodier(station_hydro, S_km2, S_jauge_km2)
        Qdmax = canal_trapezoidal(b, y, z, S, n)
        j = [31, 29, 31, 30, 31, 30, 31, 31,30, 31, 30, 31]
        ressource = []
        for i in range(12):
            Qp = Qi[i]  # le débit de pointe est le débit calculé
            f = lambda t: hydrogramme_crue(t, Tc, Qp, Qdmax)*j[i]
            g = integrale_trapeze(f, 0, 4*Tc, 1000)
            ressource.append(g)
        return ressource


# ================================================================
if __name__ == "__main__":
    # --- EXEMPLE DE CALCUL POUR ressource_crue ---
    # Données d'entrée pour la station hydrologique (débits mensuels en m3/s)
    station_hydro_exemple = [
        15.2, 12.8, 18.5, 25.3, 45.7, 62.1,
        78.4, 65.2, 48.9, 32.6, 22.4, 17.1
    ]
    S_km2 = 50.0
    S_jauge_km2 = 80.0
    b, y, z, S_pente, n_mann, Tc = 0.6, 0.6, 1, 0.001, 0.015, 1.5

    print("\n=== EXEMPLE ressource_crue ===")
    resultats = ressource_crue(Tc, b, y, z, S_pente, n_mann,
                               station_hydro_exemple, S_km2, S_jauge_km2)
    periodes = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jui",
                "Jul", "Aou", "Sep", "Oct", "Nov", "Dec"]
    for i, periode in enumerate(periodes):
        print(f"{periode}: {resultats[i]:.2f} m³")
