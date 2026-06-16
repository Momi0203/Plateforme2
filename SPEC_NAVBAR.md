# Spécification — Mise à jour barre de navigation (base.html)

## Rôles utilisateurs

| Rôle | Niveau |
|---|---|
| administrateur | Chef des opérateurs et éditeurs — accès complet |
| opérateur | Accès analyse + diagnostic + plan d'action |
| éditeur | Accès diagnostic + plan d'action |
| visiteur | Accueil + carte + à propos uniquement |

Ajouter `administrateur` aux choices du champ `role` dans `compte/models.py`.

---

## Structure navbar par rôle

| Rôle | Éléments visibles |
|---|---|
| Non authentifié | Accueil · Carte · À propos · `[FR / عربي]` · Connexion · Inscription |
| Visiteur | Accueil · Carte · À propos · `[FR / عربي]` · Profil · Déconnexion |
| Éditeur | Accueil · Carte · Diagnostic · Plan d'action · **Système** · **Requête** · Profil · Déconnexion |
| Opérateur | Accueil · Carte · Diagnostic · Étude hydrologique · Analyse · Plan d'action · **Système** · **Requête** · Profil · Déconnexion |
| Administrateur | (tout opérateur) + **Système** (vue complète) · **Requête** |

---

## Bouton "Système"

Bouton unique dans la navbar, contenu différent selon le rôle (trois vues backend distinctes).

**Vue Administrateur :**
- Suivi de l'équipe et des comptes
- Création et assignation de tâches aux agents
- Messagerie interne vers opérateurs / éditeurs

**Vue Opérateur & Éditeur :**
- Tâches déléguées par l'administrateur
- Choix / acceptation d'une tâche
- Messages reçus de l'administrateur

## Bouton "Requête"

Visible pour tous les utilisateurs authentifiés (tous rôles).
Permet de déclarer un problème sur la plateforme ou une demande sur un périmètre agricole.

---

## Modifications de la navbar existante

- **Renommer** "Analyse hydrologique" → "Étude hydrologique" (dans le dropdown Analyse)
- **Supprimer** le dropdown "Dimensionnement" (sera défini ultérieurement)
- **Ajouter** Plan d'action au rôle éditeur (actuellement opérateur seulement)

## Sécurité barre de navigation

- Supprimer les labels `dd-role` "Éditeur & Opérateur" / "Opérateur" visibles dans les dropdowns
- Le bouton "Système" n'affiche aucune mention de rôle, d'utilisateurs ou de droits
- Les vues liées à "Système" doivent être protégées côté backend (décorateur `@role_required`)

## Bouton FR / عربي (visiteurs et non authentifiés)

- Bouton de changement de langue visible uniquement pour `visiteur` et utilisateurs non authentifiés
- Implémentation via Django i18n (`LocaleMiddleware`, fichiers `.po`/`.mo` dans `locale/ar/`)
- Ajouter `dir="rtl"` sur `<html>` quand la langue active est l'arabe
- Traduire les chaînes de `base.html` et des templates visiteur uniquement dans un premier temps

---

## Prompt Claude — exécution

```
Dans le projet Django plateformeSIG, applique les modifications suivantes sur base.html et compte/models.py :

1. Ajouter 'administrateur' aux choices du champ `role` dans compte/models.py et générer la migration correspondante.

2. Dans base.html — navbar :
   a. Renommer "Analyse hydrologique" en "Étude hydrologique" dans le dropdown Analyse.
   b. Supprimer entièrement le dropdown "Dimensionnement".
   c. Rendre le dropdown "Plan d'action" visible aussi pour le rôle éditeur (actuellement opérateur seulement).
   d. Supprimer les labels dd-role ("Éditeur & Opérateur", "Opérateur") visibles dans tous les dropdowns.
   e. Ajouter un bouton "Système" dans nav-auth (après Profil, avant Déconnexion) :
      - Visible pour administrateur, opérateur, éditeur.
      - Lien href="#" pour l'instant (vues à créer ultérieurement).
      - Icône : fa-sliders-h pour admin, fa-tasks pour opérateur/éditeur.
   f. Ajouter un bouton "Requête" dans nav-auth :
      - Visible pour tous les utilisateurs authentifiés.
      - Lien href="#" pour l'instant.
      - Icône : fa-flag.
   g. Ajouter un bouton langue [FR | عربي] dans nav-auth :
      - Visible uniquement pour visiteur et utilisateurs non authentifiés.
      - Utiliser la vue Django set_language (i18n) avec un form POST.
      - Icône : fa-globe.

3. Activer Django i18n dans settings.py :
   - USE_I18N = True
   - Ajouter 'django.middleware.locale.LocaleMiddleware' dans MIDDLEWARE (après SessionMiddleware).
   - Ajouter LANGUAGES = [('fr', 'Français'), ('ar', 'العربية')].
   - Ajouter LOCALE_PATHS = [BASE_DIR / 'locale'].
   - Ajouter le tag {% load i18n %} en tête de base.html et entourer les chaînes statiques de {% trans "..." %}.

4. Dans urls.py principal, ajouter i18n_patterns et l'URL set_language.

Respecter les conventions existantes du projet (nommage français, pas de commentaires inutiles, préserver le bloc PROJ en tête de settings.py).
```
