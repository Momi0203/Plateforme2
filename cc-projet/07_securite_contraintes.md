---
section: "07"
titre: "Sécurité, contraintes et évolutivité"
version: "2.0"
date: "2026-06-04"
tags: [sécurité, rôles, contraintes, évolutivité, dépendances]
---

# §8 — Sécurité, §11 — Contraintes et évolutivité

---

## 8. Sécurité et gestion des droits

### 8.1 Matrice des rôles

| Fonctionnalité | visiteur | opérateur | éditeur |
|---|---|---|---|
| Consultation carte (toutes couches) | OUI | OUI | OUI |
| Requête simple et sélection | NON | OUI | OUI |
| Requête multicritère et spatiale | NON | OUI | OUI |
| Outils d'analyse (tampon, intersection…) | NON | OUI | OUI |
| Boîtes outils métier (scoring, efficience…) | NON | OUI | OUI |
| Export CSV / Excel / GeoJSON | NON | OUI | OUI |
| Export cartographique PDF/PNG | NON | OUI | OUI |
| Sauvegarde styles symbologie | NON | OUI | OUI |
| Sauvegarde requêtes nommées | NON | OUI | OUI |
| Édition cellule tableau attributaire | NON | NON | OUI |
| Persistance couches résultats d'outils | NON | NON | OUI |

### 8.2 Implémentation des rôles

```python
# compte/decorators.py (à créer — comble le gap sécurité actuel)
from functools import wraps
from django.http import HttpResponseForbidden

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('connexion')
            if request.user.role not in roles:
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

# Usage dans carte/api_views.py
@login_required
@role_required('operateur', 'editeur')
def api_requete_simple(request): ...
```

### 8.3 Exigences sécurité

| ID | Exigence |
|---|---|
| SEC-01 | Tous les endpoints `/carte/api/*` : `@login_required`. HTTP 403 si non autorisé. |
| SEC-02 | Ajouter `@role_required` sur les vues opérateur/éditeur. |
| SEC-03 | Protection CSRF sur tous les POST. |
| SEC-04 | Validation côté serveur des GeoJSON entrants (format, SRID, taille max 5 Mo). |
| SEC-05 | Requêtes SQL avancées : passer par l'ORM ou liste blanche — jamais SQL brut. |
| SEC-06 | Fichiers exportés : générés en mémoire + streaming, pas de fichiers temporaires. |

---

## 11. Contraintes et dépendances

### 11.1 Contraintes techniques

| Contrainte | Impact sur le code |
|---|---|
| GDAL 3.12 via OSGeo4W déjà installé | Utiliser GeoDjango pour les opérations vectorielles. Pas d'ajout de Shapely/Fiona/Geopandas. |
| SRID 4326 en base | GeoJSON retournés en 4326. Calculs métriques → `.transform(26191)` avant calcul. |
| Django 6 — pas de DRF | Vues Django standard + `JsonResponse`. |
| Calendrier Sep→Août | Graphiques séries mensuelles : axe X = [Sep, Oct, Nov, Déc, Jan, Fév, Mar, Avr, Mai, Jun, Jul, Aoû]. |
| Champ `statut` sur ouvrages | Symbologie par défaut : `valide` = bleu plein, `non_valide` = bleu hachuré. |

### 11.2 Dépendances inter-apps

| App | Dépendance |
|---|---|
| `diagnostic` | Fournit 7 types d'ouvrages + périmètres. Ne pas modifier leurs modèles. |
| `analyse_hydrologique` | Fournit BV, stations, réseau hydro. Résultats crues disponibles pour dashboard. |
| `Besions_Ressources` | Fournit stations clim + bilans mensuels. |
| `compte` | Fournit `Utilisateur.role` pour les droits d'accès. |
| `efficiences` (futur) | Quand développé, ses couches seront disponibles via LAYER_REGISTRY si elles ont un champ `geometrie`. |

---

## 11.3 Exigence fondamentale — Évolutivité

> **Critère de conception le plus important du module Carte.**

La base de données utilise des listes de choix Django (`CHOICES`) qui **évoluent dans le temps** :
nouvelles natures de matériaux, nouveaux types d'ouvrages, nouvelles sources d'énergie…

**Règle absolue : aucune valeur de liste de choix ne doit être codée en dur dans le JavaScript.**

| Composant | Règle | Mauvais ❌ | Bon ✓ |
|---|---|---|---|
| Symbologie catégorisée | Lire les valeurs depuis l'API | `if nature === 'béton'` dans le JS | `fetch('/carte/api/couche/troncons_seguias/champs/nature/valeurs/')` |
| Filtres tableau | Valeurs des dropdowns depuis GROUP BY serveur | Liste statique dans le HTML | Requête Django `TronconSeguia.objects.values_list('nature', flat=True).distinct()` |
| Requête simple auto-complétion | Valeurs depuis endpoint | Tableau JS hardcodé | Appel `/champs/<champ>/valeurs/` |
| Dashboard catégories | Construites dynamiquement | `labels: ['béton', 'terre']` en dur | Labels issus de la réponse API |
| Formulaires scoring | Critères depuis introspection modèle | Champs figés dans le JS | Champs lus depuis l'API |

### Implémentation de l'endpoint valeurs dynamiques

```python
# carte/api_views.py
@login_required
def api_champ_valeurs(request, nom_couche, nom_champ):
    """Retourne les valeurs distinctes d'un champ + libellés depuis les CHOICES."""
    layer_config = LAYER_REGISTRY.get(nom_couche)
    if not layer_config:
        return JsonResponse({'error': 'Couche inconnue'}, status=404)

    model = apps.get_model(layer_config['model'])
    field = model._meta.get_field(nom_champ)

    # Si le champ a des CHOICES, retourner valeurs + libellés
    if hasattr(field, 'choices') and field.choices:
        valeurs = [{'valeur': v, 'label': l} for v, l in field.choices]
    else:
        # Sinon, valeurs distinctes en base
        qs = model.objects.values_list(nom_champ, flat=True).distinct().order_by(nom_champ)
        valeurs = [{'valeur': v, 'label': str(v)} for v in qs if v is not None]

    return JsonResponse({'valeurs': valeurs})
```
