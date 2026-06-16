# Idéation — Mise à jour des templates (3 apps)
**Date :** 2026-06-08  
**Apps concernées :** `analyse_hydrologique` · `Besions_Ressources` · `efficiences`  
**Phase :** Idéation (sans coding)

---

## Problème 1 — Espace vide à droite (layout)

### Cause
Les templates de résultats/formulaires ont un `max-width` trop restrictif sur écran large :

| Template | Ligne | Valeur actuelle |
|---|---|---|
| `analyse_hydrologique/analyse/resultat.html` | L10 | `max-width: 1100px` |
| `besions_ressources/bilan_detail.html` | L9 | `max-width: 1280px` |
| `efficiences/formulaire_efficience.html` | L9 | `max-width: 1280px` |

Les pages d'accueil (`liste_perimetres.html`, `home.html`) n'ont **pas** ce problème.

### Solution retenue : Layout 2 colonnes avec carte sticky

```
┌─────────────────────────────────┬──────────────────┐
│  Contenu principal (70%)        │  Carte géo (30%) │
│  - KPI cards                    │  (position:sticky)│
│  - Tableaux de résultats        │                  │
│  - Sections accordéon           │  Leaflet map     │
│  - Graphiques Chart.js          │  + contrôles     │
│                                 │  basemap         │
└─────────────────────────────────┴──────────────────┘
```

**Avantage :** la carte reste visible pendant tout le scroll du résultat.  
**Breakpoint mobile :** passer en colonne unique sous 1024px.

### Fichiers à modifier
- `plateformeSIG/templates/analyse_hydrologique/analyse/resultat.html`
- `plateformeSIG/templates/besions_ressources/bilan_detail.html`
- `plateformeSIG/efficiences/templates/efficiences/formulaire_efficience.html`

---

## Problème 2 — Affichage des périmètres (efficiences + besions_ressources)

### État actuel

**Efficiences** (`liste_perimetres.html`) :
- Grille de cards, une card par périmètre
- Bouton "Calculer" direct → va au formulaire vide

**Besions_Ressources** (`home.html`) :
- Grille de modules + table des derniers bilans global
- Pas de vue consolidée par périmètre

### Comportement attendu : Accordion par périmètre

```
┌─────────────────────────────────────────────────────┐
│ [🔍 Rechercher un périmètre...]                     │
└─────────────────────────────────────────────────────┘

┌─ Périmètre A  ·  3 calculs  ·  dernier: 08/06/2026 ─┐
│  [▶ Afficher]                        [+ Nouveau]    │
└─────────────────────────────────────────────────────┘

┌─ Périmètre B  ·  1 calcul  ·  dernier: 01/06/2026 ──┐
│  [▼ Afficher]                        [+ Nouveau]    │
├─────────────────────────────────────────────────────┤
│  Date          Opérateur      Résultat   Action      │
│  08/06/2026    Mohamed E.     68,4 %     [Voir]      │
│  01/06/2026    Mohamed E.     71,2 %     [Voir]      │
└─────────────────────────────────────────────────────┘
```

### Colonnes du tableau déplié

**Efficiences :**
- Date · Ouvrage de tête · Efficience globale · E. Primaire / Secondaire / Tertiaire · Nb tronçons · Opérateur · [Voir]

**Besions_Ressources :**
- Date · Station climatique · Statut (calculé/en attente) · [Voir]

### Fichiers à modifier
- `plateformeSIG/efficiences/templates/efficiences/liste_perimetres.html`
- `plateformeSIG/templates/besions_ressources/home.html`

---

## Problème 3 — Bouton "Valider l'analyse" (enregistrer comme final)

### Contexte
L'utilisateur peut lancer un calcul exploratoire, modifier les formules incluses via les modales (Tc, Q), et recalculer — mais ces changements ne sont pas marqués comme **version finale validée**.

### Bouton à ajouter : `Valider l'analyse`

Position : dans le header de chaque page de résultats, à côté des boutons d'export.

```
[ Imprimer ]  [ Télécharger ▼ ]  [ ✔ Valider l'analyse ]  [ 🗑 ]
```

### Comportement par app

| App | Template | Action serveur |
|---|---|---|
| Analyse hydrologique | `resultat.html` | Sauvegarde formules sélectionnées + Q finaux, passe `statut = 'valide'` |
| Bilan B/R | `bilan_detail.html` | `est_calcule = True` + `date_calcul = now()` |
| Efficiences | partial `resultats.html` | Persiste l'`Efficience` en DB avec `statut = 'valide'` |

### Pré-remplissage automatique (Efficiences)

Quand l'utilisateur clique **"Nouveau calcul"** pour un périmètre ayant déjà un calcul validé :
- Cocher automatiquement les mêmes séguias que le dernier calcul validé
- Pré-sélectionner le même ouvrage de tête
- L'utilisateur peut modifier avant de lancer

```python
# Vue : formulaire_efficience
dernier_calcul = Efficience.objects.filter(
    perimetre=perimetre,
    statut='valide'
).order_by('-date_calcul').first()
# Passer dernier_calcul au contexte → JS pré-coche les séguias
```

### Fichiers à modifier
- `plateformeSIG/templates/analyse_hydrologique/analyse/resultat.html`
- `plateformeSIG/templates/besions_ressources/bilan_detail.html`
- `plateformeSIG/efficiences/templates/efficiences/formulaire_efficience.html`
- `plateformeSIG/efficiences/templates/efficiences/partials/resultats.html`
- Vues correspondantes (`views.py` de chaque app)

---

## Problème 4 — Présentation géométrique : choix de fond de carte + couleurs

### État actuel
Fond de carte unique : OpenStreetMap, fixe dans les 3 apps.

### Sélecteur de basemap à ajouter

3 fonds de carte ESRI via le CDN Leaflet ESRI :

```javascript
// CDN à ajouter dans extra_css / extra_js
// https://cdn.jsdelivr.net/npm/esri-leaflet@3.0.12/dist/esri-leaflet.js

const basemaps = {
    "OpenStreetMap":    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {...}),
    "ESRI Topographic": L.esri.basemapLayer('Topographic'),
    "ESRI Satellite":   L.esri.basemapLayer('Imagery'),
    "ESRI Streets":     L.esri.basemapLayer('Streets'),
};
```

Contrôle de couches Leaflet (`L.control.layers`) déjà partiellement en place dans `resultat.html` — à étendre pour les 3 apps.

### Palette de couleurs harmonisée (toutes apps)

| Entité | Couleur | Hex | Opacité fill |
|---|---|---|---|
| Périmètre irrigué | Orange app | `#f0a500` | 0.18 |
| Bassin versant | Beige doré | `#d4920a` | 0.18 |
| Séguia principale | Bleu royal | `#1a6fa8` | — |
| Séguia secondaire | Bleu clair | `#5ba4cf` | — |
| Séguia tertiaire | Bleu pâle | `#9ecae1` | — |
| Ouvrage de tête (seuil, barrage…) | Rouge | `#c0392b` | 0.7 |
| Station hydro/pluvio (marker) | Vert | `#1e8449` | 0.8 |
| Réseau hydrographique (tronçon) | Bleu marine | `#1a6fa8` | gradient grid_code |

### Légende dynamique
Ajouter une légende Leaflet `L.control({ position: 'bottomright' })` affichant uniquement les couches présentes dans la carte courante.

### Fichiers à modifier
- `plateformeSIG/templates/analyse_hydrologique/analyse/resultat.html`
- `plateformeSIG/templates/besions_ressources/bilan_detail.html`
- `plateformeSIG/efficiences/templates/efficiences/formulaire_efficience.html`
- `plateformeSIG/templates/analyse_hydrologique/bv/detail.html`

---

## Problème 5 — Export PDF et Excel enrichis

### Contenu cible par app

#### Analyse hydrologique (`exporter_excel` / `exporter_pdf`)

**Excel — feuilles :**
1. **Synthèse** : nom BV, surface, pente, station pluvio, opérateur, date
2. **Temps de concentration** : toutes formules + Tc moyen retenu
3. **Montana** : coefficients a/b par période de retour
4. **Débits Q** : toutes formules + Gradex + Q finaux retenus (T10/20/50/100)
5. **Apports mensuels** : volumes m³ par mois (Sep→Aoû) pour les 3 scénarios
6. **Carte** : image PNG de la carte (bassin + réseau)

**PDF :**
- En-tête institutionnel
- Carte géométrique (PNG généré côté serveur via `matplotlib`)
- Tableaux Tc, Montana, Q finaux
- Graphique apports mensuels (image Chart.js via `canvas.toDataURL`)
- Annotations (observations + conclusions)

#### Bilan Besoins-Ressources

**Excel — feuilles :**
1. **Synthèse** : périmètre, station clim, station hydro, scénario, date
2. **Données climatiques** : T° min/max, insolation, pluie mensuelle
3. **Besoins culturaux** : Kc/Kr par culture + ETc mensuelle + surface
4. **Besoins totaux** : besoin brut mensuel + efficience réseau
5. **Ressources** : apports crue + stock barrage + débit disponible (mensuel)
6. **Bilan** : besoin vs ressource, excédent/déficit (Sep→Aoû)
7. **Carte** : PNG périmètre + réseau d'irrigation

**PDF :**
- KPI (besoin annuel, ressource annuelle, taux de satisfaction)
- Graphiques besoins/ressources par scénario
- Carte périmètre
- Tableau bilan mensuel

#### Efficiences

**Excel — feuilles :**
1. **Synthèse** : périmètre, ouvrage de tête, date, opérateur
2. **Tronçons** : nom séguia, type, longueur, débit, perte infiltration, perte vaporisation, efficience individuelle
3. **Synthèse P/S/T** : efficience par catégorie
4. **Résultat global** : efficience réseau globale
5. **Carte** : PNG réseau de séguias

**PDF :**
- En-tête + KPI globaux
- Tableau tronçons
- Cascade d'efficience (visuelle)
- Carte réseau irrigué

### Approche technique recommandée pour la carte dans les exports

**Côté serveur** (recommandé) : générer le PNG via `matplotlib` + `shapely`/`fiona` depuis les géométries PostGIS — plus robuste, pas de dépendance navigateur.

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from django.contrib.gis.geos import GEOSGeometry

def generer_carte_png(perimetre, buffer_io):
    fig, ax = plt.subplots(figsize=(8, 6))
    # tracer périmètre, séguias, ouvrage de tête...
    plt.savefig(buffer_io, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
```

**Côté client** (alternative) : `canvas.toDataURL()` sur le canvas Leaflet via `leaflet-image` — plus simple mais dépend du rendu navigateur.

### Fichiers à modifier / créer
- `plateformeSIG/analyse_hydrologique/views.py` (fonctions `exporter_excel`, `exporter_pdf`)
- `plateformeSIG/Besions_Ressources/views.py` (idem)
- `plateformeSIG/efficiences/views.py` (à créer)
- Nouveau module utilitaire : `plateformeSIG/static/export_carte.py`

---

## Récapitulatif des fichiers touchés

### Templates

| Fichier | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| `analyse_hydrologique/analyse/resultat.html` | ✓ | — | ✓ | ✓ |
| `besions_ressources/bilan_detail.html` | ✓ | — | ✓ | ✓ |
| `efficiences/formulaire_efficience.html` | ✓ | — | ✓ | ✓ |
| `efficiences/liste_perimetres.html` | — | ✓ | — | — |
| `besions_ressources/home.html` | — | ✓ | — | — |
| `efficiences/partials/resultats.html` | — | — | ✓ | — |
| `analyse_hydrologique/bv/detail.html` | — | — | — | ✓ |

### Vues (Python)

| Fichier | Problème | Action |
|---|---|---|
| `analyse_hydrologique/views.py` | P3, P5 | Endpoint valider + export enrichi |
| `Besions_Ressources/views.py` | P3, P5 | Endpoint valider + export enrichi |
| `efficiences/views.py` | P2, P3, P5 | Accordion data + valider + export |

---

## Ordre de priorité d'implémentation

| # | Problème | Impact utilisateur | Effort estimé |
|---|---|---|---|
| 1 | Layout 2 colonnes (P1) | ⭐⭐⭐ Fort | 🔧 Moyen |
| 2 | Accordion périmètres (P2) | ⭐⭐⭐ Fort | 🔧 Moyen |
| 3 | Basemaps ESRI + couleurs (P4) | ⭐⭐ Moyen | 🔨 Faible |
| 4 | Bouton "Valider" + pré-remplissage (P3) | ⭐⭐ Moyen | 🔧 Moyen |
| 5 | Export PDF/Excel enrichi avec carte (P5) | ⭐⭐⭐ Fort | 🔨🔨 Élevé |
