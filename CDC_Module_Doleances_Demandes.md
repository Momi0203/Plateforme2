# Cahier des Charges — Module **Doléances & Demandes**
## Plateforme HydroPlan SIG — ORMVA Tafilalet / Midelt
**Version :** 1.0  
**Date :** Juin 2026  
**Statut :** Idéation / Conception  

---

## Table des matières

1. [Présentation générale et contexte](#1-présentation-générale-et-contexte)
2. [Objectifs](#2-objectifs)
3. [Types de requêtes et profils d'émetteurs](#3-types-de-requêtes-et-profils-démetteurs)
4. [Modèles de données](#4-modèles-de-données)
5. [Fonctionnalités détaillées](#5-fonctionnalités-détaillées)
6. [Workflow de traitement — états et transitions](#6-workflow-de-traitement--états-et-transitions)
7. [Matrice des droits](#7-matrice-des-droits)
8. [Architecture technique](#8-architecture-technique)
9. [Exigences non fonctionnelles](#9-exigences-non-fonctionnelles)
10. [Critères d'acceptation](#10-critères-dacceptation)
11. [Livrables et planning indicatif](#11-livrables-et-planning-indicatif)

---

## 1. Présentation générale et contexte

### 1.1 Contexte institutionnel

L'ORMVA du Tafilalet (Office Régional de Mise en Valeur Agricole) gère les périmètres irrigués des vallées Ziz, Rheris et Maïder en zone aride. La plateforme HydroPlan SIG centralise les données hydrauliques, les diagnostics d'ouvrages et les bilans eau/besoins de ces périmètres.

La multiplicité des acteurs de terrain — AUEA, agents ORMVA, agriculteurs, gardes hydrauliques, communes rurales — génère un flux continu de signalements, demandes et réclamations dont le traitement est aujourd'hui dispersé (appels téléphoniques, courriers papier, interventions informelles). Ce module vise à structurer et tracer ces échanges au sein de la plateforme.

### 1.2 Positionnement dans la plateforme

Le module **Doléances & Demandes** est transversal : il n'appartient à aucun domaine métier spécifique mais croise toutes les entités existantes (périmètre, ouvrage, utilisateur, bilan). Il est accessible depuis la barre de navigation principale pour tout utilisateur authentifié.

### 1.3 Périmètre fonctionnel

Le module couvre trois familles de requêtes :

| Famille | Code | Description courte |
|---|---|---|
| Signalement plateforme | `TYPE_PLATEFORME` | Bug, erreur de données, accès refusé |
| Demande d'utilisation | `TYPE_ACCES` | Création compte, changement de rôle, accès à un périmètre |
| Requête périmètre agricole | `TYPE_PERIMETRE` | Problème terrain sur un ouvrage ou la distribution d'eau |

---

## 2. Objectifs

| ID | Objectif |
|---|---|
| OBJ-1 | Centraliser tous les signalements et demandes liés à la plateforme et aux périmètres dans un canal unique et traçable |
| OBJ-2 | Associer chaque requête terrain à son périmètre et, si applicable, à un ouvrage précis (seuil, seguia, khettara, etc.) |
| OBJ-3 | Mettre en place un workflow de traitement clair (soumission → assignation → traitement → clôture) avec historique des statuts |
| OBJ-4 | Permettre aux émetteurs de terrain (AUEA, agriculteurs, gardes hydrauliques) de soumettre une requête sans nécessairement disposer d'un rôle technique avancé |
| OBJ-5 | Offrir aux administrateurs et opérateurs un tableau de bord de suivi des requêtes ouvertes, filtrables par type, périmètre et urgence |
| OBJ-6 | Servir de source de données pour le module Plan d'Action (requêtes critiques → action corrective dans le calendrier d'intervention) |

---

## 3. Types de requêtes et profils d'émetteurs

### 3.1 Type I — Signalement plateforme (`TYPE_PLATEFORME`)

**Définition :** Tout dysfonctionnement ou incohérence constaté dans l'application elle-même.

**Sous-types indicatifs :**
- Bug d'affichage / calcul incorrect
- Donnée erronée sur un périmètre ou ouvrage
- Accès refusé à une fonctionnalité
- Lenteur ou indisponibilité d'une page

**Émetteurs attendus :** Tout utilisateur authentifié (visiteur, opérateur, éditeur, administrateur).

**Destinataire du traitement :** Administrateur plateforme.

---

### 3.2 Type II — Demande d'utilisation / accès (`TYPE_ACCES`)

**Définition :** Demande liée à la gestion des comptes et des droits.

**Sous-types indicatifs :**
- Création d'un nouveau compte utilisateur
- Upgrade de rôle (visiteur → opérateur)
- Rattachement à un périmètre spécifique
- Demande d'export ou de rapport particulier

**Émetteurs attendus :** Visiteurs souhaitant un accès étendu, chefs de secteur ORMVA, responsables AUEA.

**Destinataire du traitement :** Administrateur plateforme.

---

### 3.3 Type III — Requête périmètre agricole (`TYPE_PERIMETRE`) *(principale)*

**Définition :** Signalement d'un problème terrain affectant un périmètre irrigué ou un ouvrage hydraulique.

**Sous-types indicatifs :**

| Code | Libellé | Ouvrage(s) concerné(s) |
|---|---|---|
| PROB-01 | Rupture / brèche d'ouvrage | Seuil, MurProtection, BarrageRetenue |
| PROB-02 | Fuite ou colmatage de canal | Seguia |
| PROB-03 | Panne de pompe / forage | ForagePuits |
| PROB-04 | Tarissement ou débit insuffisant | Khettara, PriseLocale |
| PROB-05 | Conflit de tour d'eau | Périmètre (sans ouvrage spécifique) |
| PROB-06 | Déficit hydrique critique (sécheresse) | Périmètre |
| PROB-07 | Détérioration suite à crue | Tout ouvrage |
| PROB-08 | Obstruction par sédiments / dépôts | Seguia, Khettara |
| PROB-09 | Vandalisme ou intrusion | Tout ouvrage |
| PROB-10 | Autre problème terrain | — |

---

### 3.4 Profils d'émetteurs ORMVA Tafilalet

Le module doit permettre à l'émetteur de déclarer son profil institutionnel, en complément de son compte utilisateur :

| Code | Profil d'émetteur | Description |
|---|---|---|
| `AUEA` | Responsable AUEA | Association des Usagers de l'Eau Agricole — interface légale ORMVA/fellahs (loi 36-15 sur l'eau) |
| `AGRICULTEUR` | Agriculteur / Fellah | Usager direct des infrastructures d'irrigation |
| `AGENT_ORMVA` | Agent ORMVA | Personnel technique de l'office (hydraulicien, ingénieur, technicien) |
| `CHEF_SECTEUR` | Chef de secteur ORMVA | Responsable géographique d'un secteur d'irrigation |
| `GARDE_HYDRAULIQUE` | Garde hydraulique | Surveillant de réseau, premier constat de terrain |
| `COMMUNE` | Représentant de commune | Communes rurales pour ouvrages relevant du domaine communal |
| `BUREAU_ETUDES` | Bureau d'études / Consultant | Pour requêtes documentaires ou d'accès à des données |
| `AYANT_DROIT_KHETTARA` | Actionnaire de khettara | Communauté d'ayants droit sur une galerie drainante traditionnelle |
| `AUTRE` | Autre | Profil non listé ci-dessus |

> **Note :** Les khettaras du Tafilalet impliquent des communautés d'ayants droit (`AYANT_DROIT_KHETTARA`) sans personnalité morale formelle. Le champ texte libre `organisation` permet de préciser le nom de la communauté ou de l'association.

---

## 4. Modèles de données

### 4.1 Modèle principal `Requete`

```
Requete
├── id (PK, auto)
├── reference (CharField, auto-généré : "DD-YYYY-NNNN")
├── titre (CharField, max_length=200)
├── type_requete (CharField, choices=TYPE_REQUETE_CHOICES)
│       TYPE_PLATEFORME / TYPE_ACCES / TYPE_PERIMETRE
├── sous_type (CharField, choices=SOUS_TYPE_CHOICES, nullable)
│       PROB-01..10 pour TYPE_PERIMETRE
├── description (TextField)
├── urgence (CharField, choices=URGENCE_CHOICES)
│       faible / normale / haute / critique
├── statut (CharField, choices=STATUT_CHOICES)
│       soumise / en_cours / en_attente / traitee / cloturee / rejetee
│
├── ── Émetteur ──
├── emetteur (FK → compte.Utilisateur, null=True, blank=True)
├── type_emetteur (CharField, choices=EMETTEUR_CHOICES)
├── nom_emetteur (CharField, max_length=150, si émetteur non connecté)
├── contact_emetteur (CharField, email ou téléphone, nullable)
├── organisation (CharField, max_length=200, nullable)
│
├── ── Localisation métier ──
├── perimetre (FK → diagnostic.Perimetre, null=True, blank=True)
├── ouvrage_type (CharField, choices=OUVRAGE_TYPE_CHOICES, nullable)
│       seuil / mur_protection / seguia / barrage / khettara / forage / prise_locale
├── ouvrage_id (PositiveIntegerField, nullable)
│
├── ── Traitement ──
├── assignee (FK → compte.Utilisateur, null=True, blank=True, related_name='requetes_assignees')
├── reponse (TextField, nullable)
├── date_soumission (DateTimeField, auto_now_add=True)
├── date_traitement (DateTimeField, nullable)
├── date_cloture (DateTimeField, nullable)
└── date_modification (DateTimeField, auto_now=True)
```

**Méthode helper :** `get_ouvrage()` → retourne l'instance ORM de l'ouvrage via `ouvrage_type` + `ouvrage_id` (même pattern que `BilanOuvrageAssocie` et `Efficience`).

---

### 4.2 Modèle `CommentaireRequete`

```
CommentaireRequete
├── id (PK)
├── requete (FK → Requete, on_delete=CASCADE)
├── auteur (FK → compte.Utilisateur)
├── contenu (TextField)
├── interne (BooleanField, default=False)
│       True = visible uniquement par le staff (opérateur/éditeur/admin)
└── date_creation (DateTimeField, auto_now_add=True)
```

---

### 4.3 Modèle `HistoriqueStatut`

```
HistoriqueStatut
├── id (PK)
├── requete (FK → Requete, on_delete=CASCADE)
├── statut_precedent (CharField)
├── statut_nouveau (CharField)
├── auteur (FK → compte.Utilisateur)
├── commentaire (CharField, max_length=500, nullable)
└── date (DateTimeField, auto_now_add=True)
```

---

### 4.4 Modèle `PieceJointeRequete`

```
PieceJointeRequete
├── id (PK)
├── requete (FK → Requete, on_delete=CASCADE)
├── fichier (FileField, upload_to='doleances/pj/%Y/%m/')
├── nom_original (CharField, max_length=255)
├── taille_ko (PositiveIntegerField)
└── date_upload (DateTimeField, auto_now_add=True)
```

**Contraintes :** max 5 pièces jointes par requête ; formats autorisés : jpg, png, pdf, docx ; taille max par fichier : 10 Mo.

---

### 4.5 Constantes (choices)

```python
TYPE_REQUETE_CHOICES = [
    ('plateforme', 'Signalement plateforme'),
    ('acces', "Demande d'utilisation / accès"),
    ('perimetre', 'Requête périmètre agricole'),
]

URGENCE_CHOICES = [
    ('faible',    'Faible — aucun risque immédiat'),
    ('normale',   'Normale — à traiter sous 5 jours'),
    ('haute',     'Haute — à traiter sous 48 h'),
    ('critique',  'Critique — intervention immédiate requise'),
]

STATUT_CHOICES = [
    ('soumise',     'Soumise'),
    ('en_cours',    'En cours de traitement'),
    ('en_attente',  "En attente d'informations complémentaires"),
    ('traitee',     'Traitée'),
    ('cloturee',    'Clôturée'),
    ('rejetee',     'Rejetée'),
]

EMETTEUR_CHOICES = [
    ('auea',                 'Responsable AUEA'),
    ('agriculteur',          'Agriculteur / Fellah'),
    ('agent_ormva',          'Agent ORMVA'),
    ('chef_secteur',         'Chef de secteur ORMVA'),
    ('garde_hydraulique',    'Garde hydraulique'),
    ('commune',              'Représentant de commune'),
    ('bureau_etudes',        "Bureau d'études / Consultant"),
    ('ayant_droit_khettara', 'Actionnaire de khettara'),
    ('autre',                'Autre'),
]
```

---

## 5. Fonctionnalités détaillées

### Axe A — Soumission de requête

| ID | Fonctionnalité | Rôles |
|---|---|---|
| F-DD-01 | Formulaire de saisie d'une nouvelle requête : type, titre, description, urgence, profil émetteur | Tous (authentifiés) |
| F-DD-02 | Sélection du périmètre concerné (liste déroulante `diagnostic.Perimetre`) — obligatoire si `TYPE_PERIMETRE` | Tous |
| F-DD-03 | Sélection de l'ouvrage concerné (dropdown conditionnel au périmètre choisi, filtré par type) — optionnel | Tous |
| F-DD-04 | Upload de pièces jointes (photos terrain, rapports) — max 5 fichiers, 10 Mo chacun | Tous |
| F-DD-05 | Attribution automatique d'une référence unique `DD-YYYY-NNNN` à la soumission | Système |
| F-DD-06 | Notification par email à l'administrateur lors de toute soumission avec urgence ≥ haute | Système |

### Axe B — Consultation et suivi (émetteur)

| ID | Fonctionnalité | Rôles |
|---|---|---|
| F-DD-07 | Liste de mes requêtes avec statut, date et référence | Tous |
| F-DD-08 | Détail d'une requête : historique des statuts, commentaires publics, réponse finale | Tous |
| F-DD-09 | Possibilité d'ajouter une précision ou pièce jointe complémentaire tant que la requête n'est pas clôturée | Émetteur |
| F-DD-10 | Indicateur visuel de délai écoulé depuis la soumission (badge couleur : vert < 48h, orange < 5j, rouge > 5j) | Émetteur |

### Axe C — Traitement administratif

| ID | Fonctionnalité | Rôles |
|---|---|---|
| F-DD-11 | Tableau de bord des requêtes ouvertes, filtrable par : type, urgence, périmètre, statut, émetteur | Opérateur, Admin |
| F-DD-12 | Assignation d'une requête à un opérateur ou technicien | Admin |
| F-DD-13 | Changement de statut avec commentaire obligatoire (traçabilité complète dans `HistoriqueStatut`) | Opérateur, Admin |
| F-DD-14 | Rédaction d'une réponse officielle visible par l'émetteur | Opérateur, Admin |
| F-DD-15 | Ajout de commentaires internes (invisibles pour l'émetteur) | Opérateur, Admin |
| F-DD-16 | Clôture d'une requête (statut `cloturee`) avec motif | Admin |
| F-DD-17 | Rejet d'une requête avec motif obligatoire | Admin |

### Axe D — Tableaux de bord et indicateurs

| ID | Fonctionnalité | Rôles |
|---|---|---|
| F-DD-18 | Compteurs : requêtes soumises / en cours / traitées / critiques non traitées (widget sur tableau de bord) | Admin |
| F-DD-19 | Carte des requêtes ouvertes géolocalisées par périmètre (marqueurs sur la carte Leaflet existante) | Admin |
| F-DD-20 | Export CSV de la liste des requêtes filtrées | Admin |

---

## 6. Workflow de traitement — états et transitions

```
  [SOUMISE]
      │
      │ (admin ou opérateur prend en charge)
      ▼
  [EN_COURS]  ◄──── (relance après EN_ATTENTE)
      │
      │ (informations manquantes → demande de précision)
      ▼
  [EN_ATTENTE]
      │
      │ (émetteur répond / délai dépassé)
      ▼
  [EN_COURS]
      │
      ├──── (problème résolu, réponse rédigée) ──────► [TRAITEE]
      │                                                     │
      │                                                     │ (admin confirme)
      │                                                     ▼
      │                                                 [CLOTUREE] ✓
      │
      └──── (hors périmètre / doublon / irrecevable) ──► [REJETEE] ✗
```

**Règles de transition :**

| De | Vers | Acteur autorisé | Commentaire obligatoire |
|---|---|---|---|
| `soumise` | `en_cours` | Opérateur, Admin | Non |
| `soumise` | `rejetee` | Admin | Oui |
| `en_cours` | `en_attente` | Opérateur, Admin | Oui (préciser ce qui manque) |
| `en_cours` | `traitee` | Opérateur, Admin | Oui (résumé de l'action menée) |
| `en_cours` | `rejetee` | Admin | Oui |
| `en_attente` | `en_cours` | Opérateur, Admin | Non |
| `traitee` | `cloturee` | Admin | Non |
| `traitee` | `en_cours` | Admin | Oui (réouverture) |

---

## 7. Matrice des droits

| Action | Visiteur | Opérateur | Éditeur | Administrateur |
|---|:---:|:---:|:---:|:---:|
| Soumettre une requête de type `TYPE_PLATEFORME` | ✓ | ✓ | ✓ | ✓ |
| Soumettre une requête de type `TYPE_ACCES` | ✓ | ✓ | ✓ | ✓ |
| Soumettre une requête de type `TYPE_PERIMETRE` | — | ✓ | ✓ | ✓ |
| Voir ses propres requêtes | ✓ | ✓ | ✓ | ✓ |
| Voir toutes les requêtes | — | ✓ | — | ✓ |
| Voir les requêtes d'un périmètre spécifique | — | ✓ | ✓ (ses périmètres) | ✓ |
| Assigner une requête | — | — | — | ✓ |
| Changer le statut | — | ✓ | — | ✓ |
| Ajouter un commentaire interne | — | ✓ | — | ✓ |
| Rédiger la réponse officielle | — | ✓ | — | ✓ |
| Clôturer / rejeter | — | — | — | ✓ |
| Exporter CSV | — | — | — | ✓ |
| Voir la carte des requêtes | — | — | — | ✓ |

> **Contrainte sécurité :** Comme les autres modules de la plateforme, le contrôle de rôle doit être implémenté **au niveau des vues** (décorateur `@role_required` ou mixin) et pas uniquement dans les templates.

---

## 8. Architecture technique

### 8.1 Application Django

- **Nom de l'app :** `doleances`
- **Préfixe URL :** `/doleances/`
- **Enregistrement dans `INSTALLED_APPS` :** `'doleances'`

### 8.2 Structure de l'app

```
doleances/
├── __init__.py
├── apps.py
├── models.py          → Requete, CommentaireRequete, HistoriqueStatut, PieceJointeRequete
├── forms.py           → RequeteForm, CommentaireForm, StatutForm
├── views.py           → liste, detail, nouvelle, traiter, changer_statut, tableau_de_bord
├── urls.py
├── admin.py
├── migrations/
│   └── 0001_initial.py
└── templates/doleances/
    ├── liste.html             → mes requêtes (émetteur)
    ├── detail.html            → détail + historique + commentaires
    ├── nouvelle.html          → formulaire de soumission
    ├── tableau_de_bord.html   → vue admin (toutes requêtes)
    └── _badge_statut.html     → fragment réutilisable (badge couleur)
```

### 8.3 URLs

```python
urlpatterns = [
    path('',                      views.liste,            name='liste'),
    path('nouvelle/',             views.nouvelle,         name='nouvelle'),
    path('<int:pk>/',             views.detail,           name='detail'),
    path('<int:pk>/statut/',      views.changer_statut,   name='changer_statut'),
    path('<int:pk>/commenter/',   views.commenter,        name='commenter'),
    path('tableau-de-bord/',      views.tableau_de_bord,  name='tableau_de_bord'),
    path('export-csv/',           views.export_csv,       name='export_csv'),
]
```

**Inclusion dans `plateformeSIG/urls.py` :**
```python
path('doleances/', include('doleances.urls', namespace='doleances')),
```

### 8.4 Intégration avec les modules existants

| Module existant | Point d'intégration |
|---|---|
| `diagnostic.Perimetre` | FK dans `Requete.perimetre` — liste déroulante dans le formulaire |
| Ouvrages (`Seuil`, `Seguia`, etc.) | Référence polymorphe `ouvrage_type` + `ouvrage_id` (même pattern que `Efficience`) |
| `compte.Utilisateur` | FK émetteur + assignee + auteur commentaires |
| `plan_action` (futur) | Les requêtes critiques clôturées peuvent être converties en `ActionPlan` |

### 8.5 Notifications email

- Signal `post_save` sur `Requete` : envoi email admin si `urgence in ['haute', 'critique']`
- Signal `post_save` sur `HistoriqueStatut` : notification à l'émetteur à chaque changement de statut
- Utilise `django.core.mail.send_mail` avec les settings SMTP existants

---

## 9. Exigences non fonctionnelles

| ID | Catégorie | Exigence |
|---|---|---|
| NFR-01 | Performance | La liste des requêtes (tableau de bord) doit se charger en < 1,5 s pour 500 requêtes (utiliser `select_related` + pagination 25/page) |
| NFR-02 | Sécurité | Contrôle de rôle au niveau vue + CSRF sur tous les formulaires. Un utilisateur ne peut voir que ses propres requêtes (sauf admin/opérateur). |
| NFR-03 | Stockage | Les pièces jointes sont stockées dans `MEDIA_ROOT/doleances/pj/`. Ne pas servir les fichiers directement via Django en production — utiliser Nginx. |
| NFR-04 | Accessibilité | Le formulaire de soumission doit fonctionner sans JavaScript (JS améliore l'UX mais ne doit pas être requis). |
| NFR-05 | Traçabilité | Tout changement de statut doit créer une entrée `HistoriqueStatut` — jamais de mise à jour silencieuse. |
| NFR-06 | Cohérence | La référence `DD-YYYY-NNNN` est unique et immuable une fois générée. |
| NFR-07 | Internationalisation | Les labels et messages doivent être préparés pour `django.utils.translation` (même si seul le français est actif en V1). |

---

## 10. Critères d'acceptation

| ID | Scénario | Résultat attendu |
|---|---|---|
| SC-01 | Un visiteur soumet une requête `TYPE_PLATEFORME` | La requête est créée avec statut `soumise`, référence `DD-YYYY-NNNN` attribuée, confirmation affichée |
| SC-02 | Un opérateur soumet une requête `TYPE_PERIMETRE` sans sélectionner de périmètre | Le formulaire rejette la soumission avec un message d'erreur explicite |
| SC-03 | Un administrateur change le statut d'une requête | Une entrée `HistoriqueStatut` est créée, l'émetteur reçoit un email de notification |
| SC-04 | Un visiteur tente d'accéder à `/doleances/tableau-de-bord/` | Redirection vers la page de connexion ou erreur 403 |
| SC-05 | Un opérateur consulte la liste | Il ne voit que les requêtes où il est émetteur ou assigné (pas celles des autres opérateurs) |
| SC-06 | Soumission avec 6 pièces jointes | Le formulaire refuse la 6ᵉ pièce avec message d'erreur |
| SC-07 | Soumission d'une requête avec urgence `critique` | L'administrateur reçoit un email dans les 30 secondes |
| SC-08 | L'administrateur exporte les requêtes filtrées | Le fichier CSV est généré avec les colonnes : référence, type, urgence, statut, périmètre, date_soumission, émetteur |
| SC-09 | Un émetteur ajoute un commentaire à sa requête clôturée | L'action est refusée avec un message "requête clôturée" |
| SC-10 | Le modèle `Requete` est sauvegardé sans périmètre pour `TYPE_PERIMETRE` | Erreur de validation au niveau modèle (`clean()`) — pas seulement au niveau formulaire |

---

## 11. Livrables et planning indicatif

| Semaine | Livrable |
|---|---|
| S1 | Modèles `Requete`, `CommentaireRequete`, `HistoriqueStatut`, `PieceJointeRequete` + migration 0001 |
| S2 | Formulaire de soumission (`nouvelle.html`) + vue `liste` (mes requêtes) |
| S3 | Vue `detail` avec historique statuts et commentaires |
| S4 | Vues admin : `tableau_de_bord`, `changer_statut`, `commenter` (interne) |
| S5 | Notifications email (signaux Django) |
| S6 | Contrôle des droits au niveau vues + tests unitaires (SC-01 à SC-10) |
| S7 | Export CSV + intégration carte Leaflet (marqueurs périmètre) |
| S8 | Recette fonctionnelle et corrections |

**Total estimé :** 8 semaines développeur.

---

## Annexe — Intégration dans `base.html`

Le bouton dans la barre de navigation (visible pour tout utilisateur authentifié) :

```html
<a href="{% url 'doleances:liste' %}" class="nav-btn nav-btn-ghost">
    <i class="fas fa-flag"></i> Doléances & Demandes
</a>
```

> Le bouton est visible pour **tous les rôles** dès lors que l'utilisateur est connecté — la distinction se fait à l'intérieur du module (l'opérateur accède au tableau de bord, le visiteur arrive sur ses propres requêtes).

---

*Document produit dans le cadre du PFE — Plateforme HydroPlan SIG, ORMVA Tafilalet / Midelt, juin 2026.*
