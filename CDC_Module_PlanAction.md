# Cahier des Charges — Module Plan d'Action

**Date :** 2026-06-09
**Statut :** Idéation — en attente d'implémentation
**App Django :** `plan_action/` — préfixe URL `/plan/`

---

## 0. État global d'implémentation

> Ce bloc est mis à jour par Claude à chaque session de travail.
> États possibles : `TODO` · `EN_COURS` · `FAIT` · `BLOQUÉ`

| Section | État | Notes |
|---------|------|-------|
| Modèles + migrations (A1/A2/A3) | `FAIT` | migration 0001_initial |
| Admin | `FAIT` | 6 ModelAdmin enregistrés |
| CRUD Axe 1 — Plans d'aménagement | `FAIT` | list/create/detail/update/delete plan + action |
| Synthèse budgétaire + export Excel | `FAIT` | tableau croisé + 2 graphiques + .xlsx 2 feuilles |
| CRUD Axe 2 — Calendrier + formset | `FAIT` | formset dynamique JS + antérieures + cycle detection |
| Gantt (Frappe Gantt) | `FAIT` | Frappe Gantt 0.6.1 + CPM couleurs statut + ligne aujourd'hui + export PDF |
| Vue PERT + algorithme CPM | `FAIT` | vis.js Network 9.1.9, layout LR, CPM server-side, chemin critique rouge, tooltips ES/EF/LS/LF |
| CRUD Axe 3 — Suivi + upload | `FAIT` | Dashboard+alertes retard, formulaire rapport, Dropzone.js MIME/size, Lightbox2 galerie, timeline |
| Courbe S + suivi global | `FAIT` | Chart.js 4.4.0, todayLinePlugin, planned/actual series, suivi_global accordéon par plan |
| Matrice droits + sécurité | `EN_COURS` | S13 : @require_role(*ROLES_PLAN) sur 15 vues lecture ; éditeur bloqué A2 write — tests SC-11..SC-17 en cours |
| Tests SC-01..SC-10 | `FAIT` | 62 tests — HasCycle, CPM, Permission, CRUD, Excel, Gantt deps, Cycle form, Suivi+photo, Retard — 62/62 OK |
| Enregistrement dans INSTALLED_APPS + urls.py | `FAIT` | MEDIA_ROOT/URL ajouté aussi |
| S11 — ACT-16 + graphes synthèse enrichie | `FAIT` | ACT-16 modèle ; G1 commune (bar) ; G2 province (donut) dans plan_synthese ; G3 comparaison groupée dans synthese_comparaison |
| S12 — Données de test 2025/2026/2027 | `FAIT` | seed_plans_test --reset ; 3 plans × 10 actions ; 11 cal. ; 55 tâches FS ; 34 suivis |

---

## 1. Contexte et objectifs

### 1.1 Contexte

Le module « Plan d'Action » centralise la planification, la programmation et le suivi opérationnel des travaux d'aménagement hydro-agricole de la Petite et Moyenne Hydraulique (PMH) dans la zone d'action de l'ORMVA du Tafilalet (provinces de Midelt et Errachidia).

Dans le cadre de la stratégie **Génération Green 2021-2030**, l'ORMVA gère annuellement un programme couvrant environ 230 km de réseaux d'irrigation (séguias, khettaras), des seuils de dérivation, des ouvrages de protection et des interventions de modernisation.

### 1.2 Trois axes fonctionnels

| Axe | Intitulé | Objet |
|-----|----------|-------|
| A1 | Plans d'aménagement | Plans annuels d'investissement PMH classifiés par commune et type d'action |
| A2 | Calendrier d'intervention | Tâches planifiées (Gantt / PERT) avec responsables et mode de réalisation |
| A3 | Suivi d'avancement | Rapports périodiques d'avancement par acteur + pièces justificatives |

### 1.3 Objectifs

- **OBJ-1** : Vision consolidée des plans d'investissement PMH annuels par commune et type d'action
- **OBJ-2** : Planification détaillée par calendrier temporel (Gantt) et réseau de tâches (PERT)
- **OBJ-3** : Suivi multi-acteurs de l'avancement (travaux, études, procédures administratives)
- **OBJ-4** : Traçabilité des pièces justificatives (PV d'attachement, PV de réception, photos de chantier)
- **OBJ-5** : Matrice de droits à quatre niveaux cohérente avec le modèle de rôles existant
- **OBJ-6** : Détection automatique des tâches en retard et calcul du chemin critique (CPM)

---

## 2. Référentiel des types d'action PMH

Liste fixe implémentée en `choices` Django (V1). Basée sur les programmes annuels ORMVA Tafilalet.

| Code | Libellé | Unité |
|------|---------|-------|
| ACT-01 | Réhabilitation de séguias | ml |
| ACT-02 | Construction de séguias neuves | ml |
| ACT-03 | Construction de seuils de dérivation | nombre |
| ACT-04 | Réhabilitation de khettaras | ml |
| ACT-05 | Construction / réhabilitation de barrages collinaires | nombre |
| ACT-06 | Aménagement de prises d'eau locales | nombre |
| ACT-07 | Renforcement de murs de protection | ml |
| ACT-08 | Entretien et curage de canaux | ml |
| ACT-09 | Réhabilitation de forages / puits | nombre |
| ACT-10 | Irrigation localisée (goutte à goutte) | ha |
| ACT-11 | Planage et nivellement de parcelles | ha |
| ACT-12 | Aménagement de pistes d'accès | ml |
| ACT-13 | Protection contre les crues (digues, épis) | ml |
| ACT-14 | Étude technique préalable (APD / APS) | forfait |
| ACT-15 | Autre | — |
| ACT-16 | Réhabilitation de seuils de dérivation | nombre |

> **Note V2 :** Ce référentiel pourra être externalisé dans un modèle `TypeAction` administrable depuis `/admin/`.
> **V1.1 (S11) :** ACT-16 ajouté ; mise à jour des `choices` dans `models.py` (pas de migration schéma, changement de libellé uniquement).

---

## 3. Axe 1 — Plans d'aménagement

<!-- STATE_A1: TODO -->

### 3.1 Modèles

<!-- STATE_MODELS_A1: TODO -->

**`PlanAmenagement`** — plan annuel global

| Champ | Type | Contraintes |
|-------|------|-------------|
| `annee` | PositiveIntegerField | unique, plage 2000–2050 |
| `titre` | CharField(200) | — |
| `budget_total` | DecimalField(15,2) | en MAD |
| `source_financement` | CharField(choices) | Budget État / FEADER / Collectivité / Partenariat / Autre |
| `statut` | CharField(choices) | en_preparation / publie / archive |
| `description` | TextField(blank=True) | — |
| `date_creation` | DateTimeField(auto_now_add) | — |
| `cree_par` | FK → Utilisateur(null=True) | — |

**`ActionPlan`** — ligne du plan

| Champ | Type | Contraintes |
|-------|------|-------------|
| `plan` | FK → PlanAmenagement | CASCADE |
| `commune` | FK → carte.Commune | — |
| `perimetre` | FK → diagnostic.Perimetre(null=True) | optionnel |
| `type_action` | CharField(choices) | ACT-01..ACT-15 |
| `description` | TextField | — |
| `budget_prevu` | DecimalField(12,2) | en MAD |
| `superficie_concernee` | DecimalField(8,2, null=True) | ha — ACT-10, ACT-11 |
| `longueur_prevue` | DecimalField(10,2, null=True) | ml — séguias, murs, etc. |
| `statut` | CharField(choices) | programme / en_cours / realise / annule |
| `priorite` | IntegerField(choices) | 1=Haute / 2=Moyenne / 3=Basse |
| `observations` | TextField(blank=True) | — |

### 3.2 Fonctionnalités

| ID | Fonctionnalité | Priorité | État |
|----|----------------|----------|------|
| F-A1-01 | Liste paginée des plans avec indicateurs (nombre actions, budget, taux réalisation) | MUST | `TODO` |
| F-A1-02 | Filtres : commune, type_action, statut, priorité, année | MUST | `TODO` |
| F-A1-03 | Fiche détaillée plan avec toutes ses actions | MUST | `TODO` |
| F-A1-04 | Tableau de synthèse budgétaire par commune × type d'action | MUST | `TODO` |
| F-A1-05 | Export Excel du plan annuel (.xlsx via openpyxl) | MUST | `TODO` |
| F-A1-06 | Import depuis fichier Excel (template téléchargeable) | SHOULD | `TODO` |
| F-A1-07 | Barre de progression : % actions réalisées / total | MUST | `TODO` |
| F-A1-08 | Graphique camembert répartition budget par type d'action | SHOULD | `TODO` |

---

## 4. Axe 2 — Calendrier d'intervention

<!-- STATE_A2: TODO -->

### 4.1 Modèles

<!-- STATE_MODELS_A2: TODO -->

**`CalendrierIntervention`** — en-tête du calendrier d'une action

| Champ | Type | Contraintes |
|-------|------|-------------|
| `action` | OneToOneField → ActionPlan | CASCADE |
| `date_debut_prevue` | DateField | — |
| `date_fin_prevue` | DateField | — |
| `mode_realisation` | CharField(choices) | etude_interne_ormva / marche_public / appel_manifestation_interet / regie |
| `chef_projet` | FK → Utilisateur | — |
| `statut_calendrier` | CharField(choices) | brouillon / valide / cloture |
| `valide_par` | FK → Utilisateur(null=True) | admin uniquement |
| `date_validation` | DateTimeField(null=True) | — |

**`TacheIntervention`** — tâche élémentaire

| Champ | Type | Contraintes |
|-------|------|-------------|
| `calendrier` | FK → CalendrierIntervention | CASCADE |
| `code_tache` | CharField(20) | unique par calendrier (T01, T02…) |
| `nom_tache` | CharField(200) | — |
| `description` | TextField(blank=True) | — |
| `date_debut_prevue` | DateField | — |
| `date_fin_prevue` | DateField | — |
| `duree_prevue` | PositiveIntegerField | jours calendaires |
| `taches_anterieures` | ManyToManyField('self', blank=True) | dépendances Finish-to-Start |
| `responsable` | FK → Utilisateur | doit exister dans la plateforme |
| `type_suivi` | CharField(choices) | suivi_travaux / suivi_etude / suivi_administratif / realisation_etude_interne |
| `statut_tache` | CharField(choices) | non_demarree / en_cours / terminee / bloquee |

> **Note :** `taches_anterieures` implémente les dépendances **Finish-to-Start (FS)** : une tâche ne démarre qu'après la fin de toutes ses prédécesseurs.

### 4.2 Fonctionnalités — Formulaire et Gantt

| ID | Fonctionnalité | Priorité | État |
|----|----------------|----------|------|
| F-A2-01 | Formulaire avec formset Django dynamique (ajout/suppression tâches) | MUST | `TODO` |
| F-A2-02 | Champ `taches_anterieures` : liste à cocher des tâches du même calendrier | MUST | `TODO` |
| F-A2-03 | Validation côté serveur : détection des cycles (Kahn's algorithm) | MUST | `TODO` |
| F-A2-04 | Diagramme de Gantt (Frappe Gantt) : barres colorées par statut, liens FS, tâches critiques en rouge | MUST | `TODO` |
| F-A2-05 | Ligne verticale rouge « aujourd'hui » sur le Gantt | MUST | `TODO` |
| F-A2-06 | Bouton « Valider le calendrier » — admin uniquement, bloque toute modification opérateur | MUST | `TODO` |
| F-A2-07 | Notification interne au responsable lors de son affectation (badge nav, pas d'e-mail en V1) | SHOULD | `TODO` |
| F-A2-08 | Export PDF du Gantt (html2canvas côté client) | SHOULD | `TODO` |

### 4.3 Vue réseau PERT

<!-- STATE_PERT: TODO -->

Vue en lecture seule accessible depuis le calendrier validé. Implémentée avec **vis.js Network**.

| ID | Fonctionnalité | Priorité | État |
|----|----------------|----------|------|
| F-A2-09 | Graphe orienté acyclique (DAG) : nœuds = tâches, arcs = dépendances FS | MUST | `TODO` |
| F-A2-10 | Chaque nœud affiche : code, nom court, durée, statut (couleur de fond) | MUST | `TODO` |
| F-A2-11 | Calcul CPM côté serveur Django : forward pass (ES/EF) + backward pass (LS/LF) + marge totale | MUST | `TODO` |
| F-A2-12 | Chemin critique (marge = 0) : nœuds et arcs en rouge ; durée totale projet affichée | MUST | `TODO` |
| F-A2-13 | Tooltip au survol : ES, EF, LS, LF, marge totale | SHOULD | `TODO` |
| F-A2-14 | Disposition hiérarchique automatique (gauche → droite) | MUST | `TODO` |

#### Algorithme CPM (`plan_action/utils.py`)

<!-- STATE_CPM: TODO -->

```python
# Entrée : queryset TacheIntervention d'un calendrier
# Sortie : dict {tache_id: {ES, EF, LS, LF, marge, is_critical}}

# Étape 1 — Tri topologique (Kahn)
# Étape 2 — Forward pass : ES = max(EF prédécesseurs), EF = ES + durée
# Étape 3 — Backward pass : LF = min(LS successeurs), LS = LF − durée
# Étape 4 — Marge totale = LS − ES ; chemin critique = marge == 0
```

Si cycle détecté → `ValueError("Dépendance cyclique détectée.")` affichée dans le formulaire.

---

## 5. Axe 3 — Suivi d'avancement

<!-- STATE_A3: TODO -->

### 5.1 Modèles

<!-- STATE_MODELS_A3: TODO -->

**`SuiviAvancement`** — rapport périodique par tâche

| Champ | Type | Contraintes |
|-------|------|-------------|
| `tache` | FK → TacheIntervention | CASCADE |
| `auteur` | FK → Utilisateur | doit être = tache.responsable (contrôle serveur) |
| `date_rapport` | DateField | — |
| `avancement_pct` | PositiveIntegerField | 0–100 |
| `etat_bloc` | CharField(choices) | conforme / retard / bloque / termine |
| `commentaire` | TextField(blank=True) | — |
| `date_prochaine_echeance` | DateField(null=True) | — |
| `date_saisie` | DateTimeField(auto_now_add) | — |

**`PieceJustificative`** — document rattaché à un rapport

| Champ | Type | Contraintes |
|-------|------|-------------|
| `suivi` | FK → SuiviAvancement | CASCADE |
| `type_piece` | CharField(choices) | pv_attachement / pv_reception / photo_chantier / rapport_etude / note_administrative / autre |
| `fichier` | FileField | `MEDIA_ROOT/plan_action/pieces/<annee>/<action_id>/` — PDF/JPG/PNG/DOCX, max 10 Mo |
| `libelle` | CharField(200) | — |
| `date_document` | DateField(null=True) | — |
| `date_upload` | DateTimeField(auto_now_add) | — |
| `uploade_par` | FK → Utilisateur | — |

### 5.2 Fonctionnalités

| ID | Fonctionnalité | Priorité | État |
|----|----------------|----------|------|
| F-A3-01 | Dashboard par action : liste tâches + barre avancement_pct + badge etat_bloc coloré | MUST | `TODO` |
| F-A3-02 | Formulaire rapport — accessible uniquement au responsable de la tâche (contrôle serveur) | MUST | `TODO` |
| F-A3-03 | Upload multi-fichiers (Dropzone.js) : contrôle type MIME et taille avant envoi | MUST | `TODO` |
| F-A3-04 | Galerie photos (Lightbox2) : miniatures filtrées type_piece = photo_chantier | MUST | `TODO` |
| F-A3-05 | Courbe S (Chart.js) : avancement prévu vs réel cumulé | SHOULD | `TODO` |
| F-A3-06 | Timeline historique : liste chronologique des rapports d'une tâche + pièces jointes | MUST | `TODO` |
| F-A3-07 | Alerte retard : badge rouge si avancement_pct < avancement théorique à date courante | MUST | `TODO` |
| F-A3-08 | Vue synthèse globale (niveau plan) : taux d'avancement moyen pondéré toutes actions | SHOULD | `TODO` |

---

## 6. Matrice des droits

<!-- STATE_DROITS: TODO -->

| Action | Visiteur | Opérateur | Éditeur | Administrateur |
|--------|:--------:|:---------:|:-------:|:--------------:|
| Accéder au module `/plan/` | ✗ | ✓ | ✓ | ✓ |
| **A1** — Consulter plans / actions | ✗ | ✓ | ✓ | ✓ |
| **A1** — Créer / modifier un plan | ✗ | ✗ | ✗ | ✓ |
| **A1** — Supprimer un plan | ✗ | ✗ | ✗ | ✓ |
| **A2** — Consulter Gantt / PERT | ✗ | ✓ | ✓ | ✓ |
| **A2** — Créer calendrier (brouillon) | ✗ | ✓ | ✗ | ✓ |
| **A2** — Modifier tâches (brouillon) | ✗ | ✓ | ✗ | ✓ |
| **A2** — Valider calendrier | ✗ | ✗ | ✗ | ✓ |
| **A2** — Modifier calendrier validé | ✗ | ✗ | ✗ | ✓ |
| **A3** — Consulter dashboard suivi | ✗ | ✓ | ✓ | ✓ |
| **A3** — Saisir rapport (*) | ✗ | ✓ | ✓ | ✓ |
| **A3** — Upload pièces justificatives (*) | ✗ | ✓ | ✓ | ✓ |
| **A3** — Modifier rapport d'un autre | ✗ | ✗ | ✗ | ✓ |

(*) Uniquement si l'utilisateur est le `responsable` de la tâche dans le calendrier **validé** — contrôle côté serveur obligatoire, pas uniquement en template.

> **Règle transversale :** Le visiteur est redirigé vers `/compte/login/` sur tout endpoint `/plan/*`. Le module est réservé aux agents ORMVA authentifiés (opérateur, éditeur, admin).
>
> **Logique éditeur :** L'éditeur consulte et rapporte (A3 si responsable) mais ne programme pas (A1/A2 réservés à l'opérateur terrain et à l'admin). La validation A2 reste admin uniquement — acte d'engagement officiel.

---

## 7. Architecture technique

### 7.1 Structure de l'app `plan_action/`

<!-- STATE_STRUCTURE: TODO -->

```
plan_action/
├── models.py      # PlanAmenagement, ActionPlan, CalendrierIntervention,
│                  # TacheIntervention (M2M self), SuiviAvancement, PieceJustificative
├── views.py       # CRUD 3 axes + gantt_data (JSON) + pert_data (JSON) + export Excel
├── urls.py        # préfixe /plan/
├── forms.py       # PlanForm, ActionPlanForm, CalendrierForm + TacheFormSet, SuiviForm
├── utils.py       # Algorithme CPM (forward/backward pass)
├── admin.py
├── tests.py
└── templates/plan_action/
    ├── plan_list.html
    ├── plan_detail.html
    ├── plan_form.html
    ├── action_form.html
    ├── calendrier_form.html      # formset tâches dynamique
    ├── calendrier_gantt.html     # Frappe Gantt
    ├── calendrier_pert.html      # vis.js Network
    ├── suivi_dashboard.html
    ├── suivi_form.html
    └── suivi_historique.html
```

### 7.2 URLs principales

| URL | Vue | Description |
|-----|-----|-------------|
| `/plan/` | `plan_list` | Liste des plans annuels |
| `/plan/creer/` | `plan_create` | Formulaire création plan |
| `/plan/<id>/` | `plan_detail` | Détail + actions du plan |
| `/plan/<id>/modifier/` | `plan_update` | Modifier un plan |
| `/plan/<id>/action/ajouter/` | `action_create` | Ajouter une action |
| `/plan/action/<id>/calendrier/` | `calendrier_form` | Créer / éditer calendrier |
| `/plan/action/<id>/gantt/` | `calendrier_gantt` | Vue Gantt |
| `/plan/action/<id>/gantt/data/` | `gantt_data` | Endpoint JSON Frappe Gantt |
| `/plan/action/<id>/pert/` | `calendrier_pert` | Vue réseau PERT |
| `/plan/action/<id>/pert/data/` | `pert_data` | Endpoint JSON CPM (vis.js) |
| `/plan/action/<id>/valider/` | `valider_calendrier` | Validation admin (POST) |
| `/plan/tache/<id>/suivi/` | `suivi_form` | Saisir un rapport |
| `/plan/tache/<id>/suivi/liste/` | `suivi_historique` | Timeline rapports |
| `/plan/calendriers/` | `calendrier_list` | Liste de tous les calendriers |
| `/plan/suivi/` | `suivi_global` | Vue synthèse globale suivi |
| `/plan/<id>/export/excel/` | `export_plan_excel` | Export Excel plan |

### 7.3 Librairies front-end

| Besoin | Librairie | Licence |
|--------|-----------|---------|
| Gantt | Frappe Gantt (CDN) | MIT |
| Réseau PERT | vis.js Network (CDN) | MIT/Apache |
| Courbe S | Chart.js (CDN) | MIT |
| Galerie photos | Lightbox2 (CDN) | MIT |
| Upload multi-fichiers | Dropzone.js (CDN) | MIT |

### 7.4 Sécurité fichiers

<!-- STATE_SECURITE: TODO -->

- Chemin physique : `MEDIA_ROOT/plan_action/pieces/<annee>/<action_id>/<fichier>`
- Types MIME autorisés (contrôle serveur) : `application/pdf`, `image/jpeg`, `image/png`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Suppression physique via signal `post_delete` sur `PieceJustificative`

---

## 8. Exigences non fonctionnelles

| ID | Exigence | Cible | État |
|----|----------|-------|------|
| PERF-01 | Chargement liste plan (50 actions + filtres) | < 1 s | `TODO` |
| PERF-02 | Rendu Gantt 20 tâches (JSON + JS) | < 2 s | `TODO` |
| PERF-03 | Calcul CPM serveur (20 tâches) | < 0,2 s | `TODO` |
| PERF-04 | Upload fichier 10 Mo | < 5 s | `TODO` |
| SEC-01 | Tous les endpoints `/plan/*` : `@login_required` | — | `TODO` |
| SEC-02 | Contrôle `responsable` tâche côté serveur (pas uniquement template) | — | `TODO` |
| SEC-03 | Validation MIME fichiers uploadés côté serveur | — | `TODO` |
| SEC-04 | Modification calendrier validé bloquée sauf superuser | — | `TODO` |

---

## 9. Critères d'acceptation

| ID | Scénario | Résultat attendu | État |
|----|----------|-----------------|------|
| SC-01 | Admin crée plan 2026 avec 5 actions dans 3 communes | Plan visible, filtrable, taux 0 % | `TODO` |
| SC-02 | Opérateur crée calendrier : T3 dépend de T1 et T2 | Liens FS visibles sur le Gantt | `TODO` |
| SC-03 | Dépendance cyclique T2→T3 et T3→T2 | Erreur explicite dans le formulaire | `TODO` |
| SC-04 | Admin valide le calendrier | Statut = validé ; opérateur ne peut plus modifier | `TODO` |
| SC-05 | Vue PERT du calendrier SC-02 | Chemin critique en rouge ; tooltip ES/EF/LS/LF | `TODO` |
| SC-06 | Responsable T2 saisit rapport 40 % + photo | Barre avancement = 40 % ; photo en galerie | `TODO` |
| SC-07 | Opérateur non-responsable tente de saisir sur T1 | HTTP 403 | `TODO` |
| SC-08 | Tâche T2 en retard (avancement réel < théorique) | Badge rouge sur dashboard et Gantt | `TODO` |
| SC-09 | Visiteur tente `/plan/creer/` | Redirect `/compte/login/` | `TODO` |
| SC-10 | Admin exporte plan 2026 en Excel | .xlsx avec commune, type, budget, statut | `TODO` |

---

## 10. Planning indicatif (10 semaines)

| Semaine | Livrable | Axe | État |
|---------|----------|-----|------|
| S1 | Modèles + migrations + admin | A1/A2/A3 | `FAIT` |
| S2 | CRUD A1 : plans + actions + filtres | A1 | `FAIT` |
| S3 | Synthèse budgétaire + export Excel | A1 | `FAIT` |
| S4 | CRUD A2 : formulaire calendrier + formset tâches + détection cycles | A2 | `FAIT` |
| S5 | Gantt (Frappe Gantt) + données JSON + barre aujourd'hui | A2 | `TODO` |
| S6 | Vue PERT (vis.js) + algorithme CPM + chemin critique | A2 | `TODO` |
| S7 | CRUD A3 : formulaire rapport + upload multi-fichiers + galerie | A3 | `TODO` |
| S8 | Courbe S + timeline historique + alertes retard | A3 | `TODO` |
| S9 | Matrice droits complète + tests permissions + sécurité fichiers | A1/A2/A3 | `TODO` |
| S10 | Tests d'acceptation SC-01..SC-10 + corrections | A1/A2/A3 | `FAIT` |
| S11 | Actualisation types PMH (ACT-16) + graphes synthèse budgétaire enrichis | A1 | `FAIT` |
| S12 | Génération scénarios de test 2025 / 2026 / 2027 avec calendriers et suivi | A1/A2/A3 | `FAIT` |

---

## 11. S11 — Actualisation types PMH + synthèse budgétaire enrichie

<!-- STATE_S11: TODO -->

### 11.1 Objectif

Étendre le référentiel des types d'action (ajout ACT-16) et enrichir la page de synthèse budgétaire de trois graphiques analytiques complémentaires au tableau croisé existant.

### 11.2 Modification modèle — ACT-16

Dans `plan_action/models.py`, ajouter dans la liste `TYPE_ACTION_CHOICES` (avant `ACT-15 Autre`) :

```python
('ACT-16', 'Réhabilitation de seuils de dérivation'),
```

> Aucune migration de schéma n'est générée par Django pour un changement de `choices` seul. La migration `0002_act16` ne contiendra qu'une `AlterField` symbolique si on souhaite la tracer, sinon c'est suffisant d'éditer le modèle.

### 11.3 Nouveaux graphiques — synthèse budgétaire

Trois graphiques Chart.js 4.4.0 ajoutés à la vue `synthese_budgetaire` (ou nouvelle vue dédiée `/plan/<id>/synthese/` selon la taille du template).

#### Graphique G1 — Répartition budget par commune (bar horizontale)

- **Endpoint JSON :** `/plan/<id>/synthese/data/?granularite=commune`
- **Requête Django :**
  ```python
  ActionPlan.objects
      .filter(plan=plan)
      .values('commune__nom_fr')
      .annotate(budget=Sum('budget_prevu'), nb=Count('id'))
      .order_by('-budget')
  ```
- **Rendu :** `Chart.js` type `bar` horizontal — axe X = MAD, axe Y = noms communes.
- **Couleur :** palette dégradée bleu-marine → orange (`--c-dark` → `--c-accent`).

#### Graphique G2 — Répartition budget par province (donut)

- **Endpoint JSON :** `/plan/<id>/synthese/data/?granularite=province`
- **Requête Django :**
  ```python
  ActionPlan.objects
      .filter(plan=plan)
      .values('commune__province__nom_fr')
      .annotate(budget=Sum('budget_prevu'))
  ```
- **Rendu :** `Chart.js` type `doughnut` — légende à droite, tooltip affiche MAD et %.

#### Graphique G3 — Comparaison inter-plans (bar groupée)

- **Endpoint JSON :** `/plan/synthese/comparaison/?plans=<id1>,<id2>,...`
- **Paramètre :** sélecteur multi-plans dans le template (checkboxes sur la liste des plans).
- **Requête Django :**
  ```python
  PlanAmenagement.objects
      .filter(pk__in=selected_ids)
      .annotate(
          budget_total_actions=Sum('actions__budget_prevu'),
          budget_realise=Sum('actions__budget_prevu',
                             filter=Q(actions__statut='realise')),
      )
  ```
- **Rendu :** `Chart.js` type `bar` groupée — une série par plan, 2 barres (prévu / réalisé).
- **Axe X :** type d'action (ACT-01 → ACT-16) **ou** commune selon onglet actif.

### 11.4 Fonctionnalités S11

| ID | Fonctionnalité | Priorité | État |
|----|----------------|----------|------|
| F-S11-01 | Ajout ACT-16 dans `TYPE_ACTION_CHOICES` et mise à jour templates | MUST | `TODO` |
| F-S11-02 | Endpoint JSON `/plan/<id>/synthese/data/` — agrégations commune + province | MUST | `TODO` |
| F-S11-03 | Graphique G1 : répartition budget par commune (bar horizontale) | MUST | `TODO` |
| F-S11-04 | Graphique G2 : répartition budget par province (donut) | MUST | `TODO` |
| F-S11-05 | Endpoint JSON `/plan/synthese/comparaison/` — multi-plans | SHOULD | `TODO` |
| F-S11-06 | Graphique G3 : comparaison inter-plans prévu/réalisé (bar groupée) | SHOULD | `TODO` |
| F-S11-07 | Sélecteur de plans pour G3 (checkboxes, max 5 plans) | SHOULD | `TODO` |
| F-S11-08 | Export des 3 graphiques en PNG (html2canvas, bouton dédié) | COULD | `TODO` |

### 11.5 URLs nouvelles (S11)

| URL | Vue | Description |
|-----|-----|-------------|
| `/plan/<id>/synthese/data/` | `synthese_data` | JSON agrégations G1+G2 pour un plan |
| `/plan/synthese/comparaison/` | `synthese_comparaison` | JSON agrégations G3 multi-plans |

---

## 12. S12 — Génération des scénarios de test 2025 / 2026 / 2027

<!-- STATE_S12: TODO -->

### 12.1 Objectif

Peupler la base de données avec trois plans d'aménagement cohérents (2025, 2026, 2027) servant de **données de démonstration**. Les données sont fictives mais logiques et représentatives d'un programme PMH réel de l'ORMVA Tafilalet. La répartition est équitable entre communes, types d'action et priorités.

> Ces données ne reflètent pas la réalité — elles servent uniquement à valider les vues, graphiques et exports.

### 12.2 Implémentation

**Fichier :** `plan_action/management/commands/seed_plans_test.py`
**Appel :** `python manage.py seed_plans_test [--reset]`

- `--reset` : supprime les 3 plans test avant recréation (idempotent).
- Sans `--reset` : skip si le plan existe déjà (`annee` unique).
- Les communes sont récupérées depuis `carte.Commune.objects.all()`. Si aucune n'existe, le script crée 6 communes fictives avec 2 provinces.

### 12.3 Structure des données par plan

#### Plan 2025 — En cours de réalisation

| Attribut | Valeur |
|----------|--------|
| `annee` | 2025 |
| `titre` | Programme PMH Tafilalet — Exercice 2025 |
| `budget_total` | 12 000 000 MAD |
| `source_financement` | `budget_etat` |
| `statut` | `publie` |

**Actions (10) :** réparties sur 5 communes, 2 par commune, priorités mixtes.

| # | Type | Commune | Budget (MAD) | Priorité | Statut |
|---|------|---------|--------------|----------|--------|
| 1 | ACT-01 Réhab. séguias | C1 | 1 200 000 | Haute | en_cours |
| 2 | ACT-03 Construction seuil | C1 | 900 000 | Haute | en_cours |
| 3 | ACT-04 Réhab. khettaras | C2 | 800 000 | Haute | realise |
| 4 | ACT-07 Murs protection | C2 | 600 000 | Moyenne | realise |
| 5 | ACT-01 Réhab. séguias | C3 | 1 500 000 | Haute | en_cours |
| 6 | ACT-16 Réhab. seuil dérivation | C3 | 1 100 000 | Haute | en_cours |
| 7 | ACT-08 Entretien canaux | C4 | 700 000 | Moyenne | programme |
| 8 | ACT-10 Irrigation localisée | C4 | 1 800 000 | Moyenne | programme |
| 9 | ACT-09 Réhab. forages | C5 | 900 000 | Basse | programme |
| 10 | ACT-14 Étude APD | C5 | 500 000 | Basse | programme |

**Calendriers :** les 6 premières actions ont un `CalendrierIntervention` **validé** avec 4–5 tâches chacun.
**Suivi :** les actions `en_cours` ont 2–3 rapports `SuiviAvancement` (avancement 30–75 %).

#### Plan 2026 — En préparation / début exécution

| Attribut | Valeur |
|----------|--------|
| `annee` | 2026 |
| `titre` | Programme PMH Tafilalet — Exercice 2026 |
| `budget_total` | 15 000 000 MAD |
| `source_financement` | `budget_etat` |
| `statut` | `en_preparation` |

**Actions (10) :** 5 communes × 2 actions. Mix équilibré ACT-01 à ACT-16.
**Calendriers :** 5 premières actions ont un calendrier en `brouillon` (non validé), 4–5 tâches.
**Suivi :** aucun suivi (plan en préparation).

| # | Type | Commune | Budget (MAD) | Priorité | Statut |
|---|------|---------|--------------|----------|--------|
| 1 | ACT-02 Séguias neuves | C1 | 2 000 000 | Haute | programme |
| 2 | ACT-05 Barrage collinaire | C2 | 3 500 000 | Haute | programme |
| 3 | ACT-16 Réhab. seuil dérivation | C2 | 1 200 000 | Haute | programme |
| 4 | ACT-01 Réhab. séguias | C3 | 1 400 000 | Moyenne | programme |
| 5 | ACT-13 Protection crues | C3 | 900 000 | Haute | programme |
| 6 | ACT-04 Réhab. khettaras | C4 | 1 000 000 | Moyenne | programme |
| 7 | ACT-10 Irrigation localisée | C4 | 2 200 000 | Moyenne | programme |
| 8 | ACT-11 Planage parcelles | C5 | 800 000 | Basse | programme |
| 9 | ACT-06 Prises d'eau | C5 | 700 000 | Basse | programme |
| 10 | ACT-14 Étude APD | C1 | 1 300 000 | Haute | programme |

#### Plan 2027 — Prospectif

| Attribut | Valeur |
|----------|--------|
| `annee` | 2027 |
| `titre` | Programme PMH Tafilalet — Exercice 2027 (prospectif) |
| `budget_total` | 18 000 000 MAD |
| `source_financement` | `partenariat` |
| `statut` | `en_preparation` |

**Actions (10) :** orientées modernisation et irrigation localisée (axe Génération Green 2030).
**Calendriers :** aucun (plan prospectif).
**Suivi :** aucun.

| # | Type | Commune | Budget (MAD) | Priorité | Statut |
|---|------|---------|--------------|----------|--------|
| 1 | ACT-10 Irrigation localisée | C1 | 3 500 000 | Haute | programme |
| 2 | ACT-10 Irrigation localisée | C2 | 3 000 000 | Haute | programme |
| 3 | ACT-01 Réhab. séguias | C3 | 1 800 000 | Haute | programme |
| 4 | ACT-16 Réhab. seuil dérivation | C3 | 1 500 000 | Haute | programme |
| 5 | ACT-05 Barrage collinaire | C4 | 2 500 000 | Haute | programme |
| 6 | ACT-04 Réhab. khettaras | C4 | 1 000 000 | Moyenne | programme |
| 7 | ACT-07 Murs protection | C5 | 800 000 | Moyenne | programme |
| 8 | ACT-09 Réhab. forages | C5 | 700 000 | Moyenne | programme |
| 9 | ACT-12 Pistes d'accès | C1 | 1 200 000 | Basse | programme |
| 10 | ACT-14 Étude APD | C2 | 2 000 000 | Haute | programme |

### 12.4 Structure des calendriers générés

Pour chaque action avec calendrier, le script génère **4 tâches typiques** selon le type d'action :

| Code tâche | Nom | Durée | Dépend de |
|------------|-----|-------|-----------|
| T01 | Mobilisation et installations de chantier | 5 j | — |
| T02 | Travaux préparatoires (terrassement / implantation) | 10 j | T01 |
| T03 | Travaux principaux | `duree_principale` | T02 |
| T04 | Contrôle qualité et essais | 5 j | T03 |
| T05 | Réception provisoire et clôture | 3 j | T04 |

`duree_principale` par type :
- ACT-01 (séguias) : 30 j — ACT-03 / ACT-16 (seuils) : 25 j — ACT-04 (khettaras) : 35 j
- ACT-07 (murs) : 20 j — ACT-08 (canaux) : 15 j — ACT-10 (irrigation) : 45 j
- Autres : 20 j

**Dates :** début = 1er mars de l'année du plan ; fin calculée par somme des durées.
**Responsable :** le premier utilisateur `role='operateur'` trouvé en base, sinon le superuser.
**Chef de projet :** le premier superuser ou `role='administrateur'`.

### 12.5 Rapports de suivi générés (plan 2025 uniquement)

Pour les 4 actions `en_cours` du plan 2025, le script crée des rapports réalistes :

| Tâche | Rapport 1 | Rapport 2 | Rapport 3 |
|-------|-----------|-----------|-----------|
| T01 | avancement=100 %, terminee | — | — |
| T02 | avancement=100 %, terminee | — | — |
| T03 | avancement=40 %, en_cours | avancement=65 %, en_cours | — |
| T04 | — | — | — |
| T05 | — | — | — |

`date_rapport` : espacés de ~15 jours à partir du 15 mars 2025.

### 12.6 Fonctionnalités S12

| ID | Fonctionnalité | Priorité | État |
|----|----------------|----------|------|
| F-S12-01 | Command `seed_plans_test` idempotente (option `--reset`) | MUST | `TODO` |
| F-S12-02 | Création plans 2025 / 2026 / 2027 avec actions équilibrées | MUST | `TODO` |
| F-S12-03 | Génération calendriers validés pour plan 2025 (T01→T05, dépendances FS) | MUST | `TODO` |
| F-S12-04 | Génération calendriers brouillon pour plan 2026 | SHOULD | `TODO` |
| F-S12-05 | Génération rapports suivi 2025 (avancement partiel, étatconforme/retard) | MUST | `TODO` |
| F-S12-06 | Création 6 communes fictives si `carte.Commune` vide | SHOULD | `TODO` |
| F-S12-07 | Message de résumé en fin d'exécution (plans créés, actions, calendriers, suivis) | MUST | `TODO` |

---

## 14. S13 — Application de la matrice de droits révisée

<!-- STATE_S13: TODO -->

### 14.1 Objectif

Mettre en conformité l'implémentation des droits avec la matrice validée en session (juin 2026) :

1. **Visiteur** : aucun accès à `/plan/*` — redirect login (était : consultation autorisée)
2. **Éditeur** : consultation + A3 si responsable — sans droit de créer/modifier A1 ou A2
3. **Validation A2** : admin uniquement (inchangé, à vérifier)

La sécurité existante (`decorators.py require_role`, `SEC-01..04`) couvre déjà la création. Cette semaine corrige uniquement les cas où la **consultation** était ouverte au visiteur et clarifie le périmètre éditeur.

---

### 14.2 Changements par fichier

#### `plan_action/decorators.py`

Vérifier que `require_role` accepte une liste de rôles ET que le visiteur est bloqué **à l'entrée du module**, pas seulement sur les actions d'écriture.

```python
# Règle globale à appliquer sur TOUTES les vues /plan/*
ROLES_AUTORISES_PLAN = ('operateur', 'editeur', 'administrateur')

# Règle restreinte pour les vues d'écriture A1 / A2
ROLES_ECRITURE_A1_A2 = ('operateur', 'administrateur')

# Règle validation A2
ROLES_VALIDATION_A2 = ('administrateur',)
```

#### `plan_action/views.py` — décorateurs à appliquer

| Vue | Décorateur actuel | Décorateur cible |
|-----|-------------------|-----------------|
| `plan_list`, `plan_detail`, `calendrier_gantt`, `calendrier_pert`, `suivi_dashboard`, `suivi_historique`, `suivi_global` | `@login_required` | `@login_required` + `@require_role(ROLES_AUTORISES_PLAN)` |
| `plan_create`, `plan_update`, `action_create`, `action_update`, `calendrier_form` | `@login_required` | `@login_required` + `@require_role(ROLES_ECRITURE_A1_A2)` |
| `plan_delete` | `@login_required` | `@login_required` + `@require_role('administrateur')` |
| `valider_calendrier` | `@login_required` | `@login_required` + `@require_role(ROLES_VALIDATION_A2)` |
| `suivi_form` | `@login_required` + check responsable | inchangé — éditeur autorisé si responsable |

#### `templates/base.html`

Le lien « Plan d'action » dans la navigation est déjà conditionné à `opérateur`. Vérifier que le visiteur ne voit pas ce lien.

---

### 14.3 Fonctionnalités S13

| ID | Fonctionnalité | Priorité | État |
|----|----------------|----------|------|
| F-S13-01 | `require_role` : bloquer visiteur sur toutes les vues lecture `/plan/*` (redirect login) | MUST | `TODO` |
| F-S13-02 | `require_role` : bloquer éditeur sur vues écriture A1/A2 (créer/modifier plan, calendrier, tâches) | MUST | `TODO` |
| F-S13-03 | `require_role` : seul admin sur `plan_delete` et `valider_calendrier` | MUST | `TODO` |
| F-S13-04 | Vérifier que `suivi_form` autorise éditeur si `request.user == tache.responsable` | MUST | `TODO` |
| F-S13-05 | Ajouter tests unitaires visiteur bloqué sur `plan_list`, `gantt`, `pert`, `suivi_dashboard` | MUST | `TODO` |
| F-S13-06 | Ajouter tests éditeur bloqué sur `plan_create`, `calendrier_form`, `valider_calendrier` | MUST | `TODO` |
| F-S13-07 | Ajouter test éditeur autorisé sur `suivi_form` quand il est responsable de la tâche | MUST | `TODO` |

---

### 14.4 Nouveaux critères d'acceptation

| ID | Scénario | Résultat attendu | État |
|----|----------|-----------------|------|
| SC-11 | Visiteur tente `GET /plan/` | Redirect `/compte/login/?next=/plan/` | `TODO` |
| SC-12 | Visiteur tente `GET /plan/1/action/1/gantt/` | Redirect login | `TODO` |
| SC-13 | Éditeur tente `GET /plan/creer/` | HTTP 403 | `TODO` |
| SC-14 | Éditeur tente `GET /plan/action/1/calendrier/` | HTTP 403 | `TODO` |
| SC-15 | Éditeur tente `POST /plan/action/1/valider/` | HTTP 403 | `TODO` |
| SC-16 | Éditeur responsable d'une tâche accède à `suivi_form` | HTTP 200 — formulaire accessible | `TODO` |
| SC-17 | Éditeur non-responsable tente `suivi_form` d'une tâche | HTTP 403 | `TODO` |

---

### 14.5 Mise à jour du tableau d'état global

Après S13, la ligne `Matrice droits + sécurité` passe de `FAIT` à `EN_COURS` jusqu'à validation des SC-11..SC-17.

---

## 13. Fichiers créés / à créer (récapitulatif)

### Fichiers existants (S1–S10)

| Fichier | Rôle | État |
|---------|------|------|
| `plan_action/__init__.py` | — | `FAIT` |
| `plan_action/models.py` | 6 modèles | `FAIT` |
| `plan_action/views.py` | ~20 vues | `FAIT` |
| `plan_action/urls.py` | patterns `/plan/` | `FAIT` |
| `plan_action/forms.py` | formulaires + formsets | `FAIT` |
| `plan_action/utils.py` | algorithme CPM | `FAIT` |
| `plan_action/admin.py` | 6 ModelAdmin | `FAIT` |
| `plan_action/apps.py` | `PlanActionConfig` | `FAIT` |
| `plan_action/decorators.py` | `require_role` | `FAIT` |
| `plan_action/tests.py` | 62 tests | `FAIT` |
| `plan_action/migrations/0001_initial.py` | migration initiale | `FAIT` |
| `plateformeSIG/settings.py` | `plan_action` dans `INSTALLED_APPS` + MEDIA | `FAIT` |
| `plateformeSIG/urls.py` | `/plan/` namespace `plan_action` | `FAIT` |
| `templates/plan_action/*.html` | 10 templates | `FAIT` |
| `templates/403.html` | page d'erreur droits | `FAIT` |

### Fichiers à créer (S11–S12)

| Fichier | Rôle | Semaine | État |
|---------|------|---------|------|
| `plan_action/views.py` | Ajouter vues `synthese_data`, `synthese_comparaison` | S11 | `TODO` |
| `plan_action/urls.py` | Ajouter routes synthèse | S11 | `TODO` |
| `templates/plan_action/synthese_graphes.html` | 3 graphiques Chart.js (G1/G2/G3) | S11 | `TODO` |
| `plan_action/management/__init__.py` | Package management | S12 | `FAIT` |
| `plan_action/management/commands/__init__.py` | Package commands | S12 | `FAIT` |
| `plan_action/management/commands/seed_plans_test.py` | Command de peuplement 2025/2026/2027 | S12 | `FAIT` |
