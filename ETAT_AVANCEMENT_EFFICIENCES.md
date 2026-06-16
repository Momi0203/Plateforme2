# ÉTAT D'AVANCEMENT — MODULE EFFICIENCES_RÉSEAUX

## Plateforme SIG — Gestion des ressources hydrauliques (Tafilalet / Midelt)

**Date du rapport :** 21 mai 2026
**Version :** 1.1
**Statut global :** Spécification consolidée — Implémentation à démarrer

---

## 1. SYNTHÈSE EXÉCUTIVE

Le module **Efficiences_Réseaux** complète la plateforme SIG existante par le calcul du rendement des réseaux hydrauliques d'irrigation. Il s'appuie sur les modèles déjà en production dans l'application `diagnostic` (Périmètre, ouvrages de tête, séguias) et introduit deux extensions ciblées :

- Un champ ET0 à ajouter sur le modèle Périmètre.
- Une nouvelle entité **Efficience** dédiée à la sauvegarde des résultats agrégés.

L'objectif fonctionnel est triple :

1. Quantifier deux types de pertes — infiltration (formule de Davis et Wilson) et évaporation (ET0).
2. Sauvegarder l'efficience calculée directement au niveau de chaque tronçon (séguia).
3. Agréger ces valeurs élémentaires en efficiences par catégorie (principale, secondaire, tertiaire) puis en efficience globale par ouvrage de tête.

**Avancement global :** 15 % (spécification rédigée et consolidée, validation utilisateur obtenue, développement non démarré).

---

## 2. POSITIONNEMENT DANS LA PLATEFORME

### 2.1 Applications déjà en production

| Application | Préfixe URL | Rôle | Statut |
|---|---|---|---|
| compte | /compte/ | Authentification, rôles utilisateurs | Opérationnelle — adaptations possibles |
| analyse_hydrologique | /hydrologie/ | Bassins versants, stations, crues | Opérationnelle — adaptations possibles |
| diagnostic | /diagnostic/ | Périmètres + 7 types d'ouvrages | Opérationnelle — extensions prévues |
| Besions_Ressources | /bilan/ | Bilan besoins / ressources | Opérationnelle — adaptations possibles |
| carte | (interne) | Géographies de référence | Opérationnelle — adaptations possibles |

**Note :** Bien que ces applications soient en production, des modifications ponctuelles (ajout de champs, nouvelles vues, ajustements de templates) restent possibles et planifiées au fil des besoins du module Efficiences et des évolutions futures de la plateforme.

### 2.2 Application à créer

| Application | Préfixe URL | Rôle | Statut |
|---|---|---|---|
| efficiences | /efficiences/ | Calcul du rendement des réseaux | À développer |

### 2.3 Modification du template de base

Le menu principal de la plateforme (fichier `templates/base.html`, dropdown « Analyse hydraulique ») contient actuellement un lien marqué :

> **Hydraulique des canaux** (lien inactif `href="#"`)

Ce lien sera renommé et activé en :

> **Efficience des réseaux** pointant vers `/efficiences/`

C'est le point d'entrée utilisateur officiel du nouveau module. Aucun autre élément du menu n'est impacté.

### 2.4 Couplage avec l'existant

Le module Efficiences réutilise les entités suivantes :

- Le modèle **Perimetre** (champ `type_de_sol` déjà présent, ajout du champ ET0 prévu).
- Le modèle **Seguias** (assimilé aux tronçons de canal — longueur, largeur miroir, hauteur eau, fruit de berge, débit, type d'écoulement, type de séguia). Ajout d'un champ stockant l'efficience calculée.
- Le modèle d'association **SguiaAssocie_OuvrageTete** pour relier une séguia à son ouvrage amont. Création et modification de ces liaisons depuis l'interface du module.
- Les ouvrages de tête existants (Seuil, PriseLocale, Khettara, ForagePuits, BarrageRetenue).

---

## 3. PÉRIMÈTRE FONCTIONNEL CIBLE

### 3.1 Fonctionnalités prévues

| Fonctionnalité | Description | Priorité |
|---|---|---|
| Liste des périmètres | Tableau de bord d'entrée du module | Haute |
| Gestion des liaisons séguia ↔ ouvrage de tête | Création et modification dans le contexte du périmètre | Haute |
| Formulaire de calcul tronçon | Sélection méthode, ouvrage, tronçon | Haute |
| Calcul AJAX par tronçon | Lancement asynchrone et affichage résultats | Haute |
| Agrégation par catégorie | Efficience principale / secondaire / tertiaire | Haute |
| Agrégation globale par ouvrage de tête | Efficience consolidée du réseau amont | Haute |
| Sauvegarde des résultats | Stockage dans la séguia et dans l'entité Efficience | Haute |
| Historique | Consultation des calculs antérieurs | Moyenne |
| Règle dalot | Pv = 0 pour les canaux fermés | Haute |
| Classification automatique | Principal / Secondaire / Tertiaire selon débit | Haute |

### 3.2 Flux de gestion des liaisons séguia ↔ ouvrage de tête

L'utilisateur opère **toujours dans le contexte d'un périmètre sélectionné**. Trois cas sont supportés :

| Cas | Action attendue |
|---|---|
| La liaison séguia ↔ ouvrage de tête existe | Lecture et affichage simple |
| La liaison n'existe pas | Création d'un nouvel enregistrement `SguiaAssocie_OuvrageTete` |
| La liaison existe mais doit évoluer | Modification du ou des ouvrages de tête associés |

Cette gestion s'opère depuis l'écran formulaire du module avant le lancement du calcul, garantissant la cohérence des données amont.

### 3.3 Hors périmètre (V1)

- Génération de rapports PDF.
- Exposition d'une API REST publique.
- Graphiques d'évolution temporelle.
- Système de notification par seuil d'alerte.
- Comparaison de scénarios.

---

## 4. MODÈLE DE DONNÉES — ÉVOLUTIONS ET CRÉATIONS

### 4.1 Extension du modèle Perimetre (ajout d'un champ)

| Champ ajouté | Type | Contraintes | Description |
|---|---|---|---|
| et0_mm_jour | FloatField | null=True, blank=True | Évapotranspiration de référence en mm/jour |

Une migration dédiée sera générée pour cette évolution. Le champ pourra être renseigné manuellement ou dérivé d'une station climatique associée au périmètre.

### 4.2 Extension du modèle Seguias (sauvegarde de l'efficience tronçon)

| Champ ajouté | Type | Contraintes | Description |
|---|---|---|---|
| efficience_calculee | DecimalField | 6, 2, null=True | Efficience du tronçon en % issue du dernier calcul |
| perte_infiltration_m3s | DecimalField | 12, 8, null=True | Perte par infiltration enregistrée |
| perte_vaporisation_m3s | DecimalField | 12, 8, null=True | Perte par évaporation enregistrée |
| date_dernier_calcul | DateTimeField | null=True | Horodatage du dernier calcul |

Ces champs sont mis à jour à chaque calcul, garantissant qu'une séguia porte toujours sa valeur d'efficience la plus récente.

### 4.3 Nouvelle entité Efficience (résultats agrégés)

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | AutoField | Clé primaire | Identifiant unique |
| perimetre | ForeignKey | Vers Perimetre, CASCADE | Périmètre concerné |
| ouvrage_tete_type | CharField | 30 | Type d'ouvrage amont (seuil, prise, khettara, forage, barrage) |
| ouvrage_tete_id | PositiveIntegerField | — | Identifiant de l'ouvrage amont |
| efficience_principale | DecimalField | 6, 2, null=True | Efficience moyenne des tronçons principaux |
| efficience_secondaire | DecimalField | 6, 2, null=True | Efficience moyenne des tronçons secondaires |
| efficience_tertiaire | DecimalField | 6, 2, null=True | Efficience moyenne des tronçons tertiaires |
| efficience_globale | DecimalField | 6, 2 | Efficience globale du réseau amont |
| nb_troncons_principaux | PositiveSmallIntegerField | default=0 | Compteur tronçons principaux |
| nb_troncons_secondaires | PositiveSmallIntegerField | default=0 | Compteur tronçons secondaires |
| nb_troncons_tertiaires | PositiveSmallIntegerField | default=0 | Compteur tronçons tertiaires |
| date_calcul | DateTimeField | auto_now_add | Horodatage |
| operateur | ForeignKey | Vers Utilisateur, SET_NULL | Opérateur ayant lancé le calcul |

Cette entité agrège les résultats au niveau d'un ouvrage de tête donné, dans le contexte d'un périmètre. Elle constitue la trace historique consultable et le support des tableaux de bord.

### 4.4 Modèles existants réutilisés sans modification

| Modèle source | Usage |
|---|---|
| diagnostic.SguiaAssocie_OuvrageTete | Liaison séguia ↔ ouvrage amont (lecture et écriture) |
| diagnostic.Seuil, PriseLocale, Khettara, ForagePuits, BarrageRetenue | Ouvrages de tête candidats |
| compte.Utilisateur | Traçabilité des opérations |

---

## 5. MÉTHODOLOGIE D'AGRÉGATION DES EFFICIENCES

### 5.1 Niveau 1 — Efficience par tronçon (séguia)

Pour chaque séguia, le calcul applique la formule de Davis et Wilson (infiltration) et la formule d'évaporation (avec règle dalot), puis calcule l'efficience individuelle :

E_troncon = (1 − (Pi + Pv) / Q_amont) × 100

Résultat sauvegardé dans la séguia elle-même (champ `efficience_calculee`).

### 5.2 Niveau 2 — Efficience par catégorie de canal

Les séguias sont catégorisées selon leur attribut `type_deguia` (Principale, Secondaire, Tertiaire). Pour chaque catégorie présente sous un ouvrage de tête donné :

**Méthode retenue : moyenne pondérée par le débit amont**

E_categorie = somme(E_troncon × Q_troncon) / somme(Q_troncon)

La pondération par le débit donne plus de poids aux tronçons à fort débit, qui sont structurants pour le bilan hydrique. Si aucun tronçon de la catégorie n'existe, l'efficience de catégorie est laissée à null.

### 5.3 Niveau 3 — Efficience globale par ouvrage de tête

L'efficience globale d'un ouvrage de tête est calculée comme le **produit en cascade** des efficiences par catégorie, traduisant la traversée successive du réseau :

E_globale = E_principale × E_secondaire × E_tertiaire

(Les valeurs sont exprimées en fraction décimale avant multiplication, puis reconverties en pourcentage.)

Si une catégorie est absente du réseau, son efficience est considérée égale à 1 (transit sans perte additionnelle dans cette strate).

### 5.4 Synthèse de la cascade

| Niveau | Granularité | Méthode | Stockage |
|---|---|---|---|
| 1 | Tronçon (séguia) | Formules Davis-Wilson et ET0 | Champ sur Seguias |
| 2 | Catégorie sous ouvrage de tête | Moyenne pondérée par débit | Champ sur Efficience |
| 3 | Ouvrage de tête | Produit en cascade des catégories | Champ sur Efficience |

---

## 6. ARCHITECTURE TECHNIQUE PRÉVUE

### 6.1 Arborescence cible

L'application suivra la structure standard Django utilisée par les autres applications de la plateforme :

- Dossier racine `efficiences/`
- Sous-dossier `services/` regroupant la logique métier (coefficients, infiltration, vaporisation, agrégation, orchestrateur)
- Sous-dossier `templates/efficiences/` avec partiels AJAX
- Sous-dossier `static/efficiences/` (CSS, JS)
- Sous-dossier `templatetags/` pour les filtres personnalisés

### 6.2 Découpage en services

| Service | Responsabilité |
|---|---|
| coefficients | Table des coefficients C par type de sol et revêtement |
| infiltration | Calcul des pertes selon Davis et Wilson |
| vaporisation | Calcul des pertes par évaporation avec règle dalot |
| efficience_troncon | Calcul de l'efficience individuelle d'un tronçon |
| agregation | Calculs niveau catégorie (moyenne pondérée) et niveau global (cascade) |
| orchestrateur | Pilotage du calcul complet et persistance |

---

## 7. RÉFÉRENTIEL DES COEFFICIENTS

### 7.1 Canaux non revêtus

| Type de sol | Coefficient C |
|---|---|
| Sols argileux | 12 |
| Sols limono-argileux | 15 |
| Sols limoneux | 20 |
| Sols sablo-limoneux | 30 |
| Sols sableux | 50 |

### 7.2 Canaux revêtus

| Revêtement | Épaisseur | Coefficient C |
|---|---|---|
| Béton | 10 cm | 1 |
| Argile compactée | 15 cm | 4 |
| Asphalte léger | — | 5 |

---

## 8. FORMULES MÉTIER

### 8.1 Formule de Davis et Wilson (pertes par infiltration)

Q = 0,45 × C × (h × P × L) / (4 000 000 + 3 650 × V × h)

**Légende :**

- Q : perte en m³/s
- C : coefficient du sol ou du revêtement
- h : hauteur d'eau (m)
- P : périmètre mouillé (m)
- L : longueur du tronçon (m)
- V : vitesse moyenne (m/s)

### 8.2 Périmètre mouillé (canal trapézoïdal)

P = b + 2 × h × racine(1 + z²)

### 8.3 Section mouillée

S = b × h + z × h²

### 8.4 Vitesse d'écoulement

V = Q_amont / S

### 8.5 Perte par évaporation

Pv = (L × P) × (ET0 / 1000 / 86400)

ET0 exprimé en mm/jour — récupéré du champ ajouté sur Perimetre.

### 8.6 Efficience tronçon

E_troncon = (1 − (Pi + Pv) / Q_amont) × 100

### 8.7 Efficience par catégorie (moyenne pondérée)

E_categorie = somme(E_troncon × Q_troncon) / somme(Q_troncon)

### 8.8 Efficience globale (cascade)

E_globale = E_principale × E_secondaire × E_tertiaire

---

## 9. RÈGLES MÉTIER

### 9.1 Règle du dalot

Lorsque le type d'écoulement d'un tronçon est « dalot » (canal fermé / busé), la perte par évaporation est forcée à 0 m³/s. Cette règle est conforme à la spécification métier validée.

### 9.2 Classification hydraulique

| Dénomination | Condition sur le débit amont | Code interne |
|---|---|---|
| Principal | Q > 1,0 m³/s | principal |
| Secondaire | 0,1 < Q ≤ 1,0 m³/s | secondaire |
| Tertiaire | Q ≤ 0,1 m³/s | tertiaire |

### 9.3 Bornes de validation

- L'efficience est bornée entre 0 % et 100 % à chaque niveau (tronçon, catégorie, global).
- Les pertes négatives sont interdites.
- Une catégorie sans tronçon est neutralisée (efficience = 100 % dans la cascade).

### 9.4 Contexte périmètre

Toutes les opérations du module se déroulent dans le contexte d'un périmètre sélectionné. Les liaisons séguia ↔ ouvrage de tête sont toujours filtrées et créées sous ce périmètre.

---

## 10. INTERFACES UTILISATEUR PRÉVUES

### 10.1 Point d'entrée

Le module est accessible depuis le menu principal de la plateforme, dropdown « Analyse hydraulique », via le lien renommé **« Efficience des réseaux »**.

### 10.2 Écrans principaux

| Écran | URL | Description |
|---|---|---|
| Liste des périmètres | /efficiences/ | Cartes Bootstrap par périmètre |
| Formulaire de calcul | /efficiences/perimetre/{id}/ | Sélection méthode, liaisons et tronçon |
| Gestion des liaisons | /efficiences/perimetre/{id}/liaisons/ | Création et modification séguia ↔ ouvrage |
| Historique global | /efficiences/historique/ | Tableau de tous les calculs (Efficience) |
| Historique par périmètre | /efficiences/historique/perimetre/{id}/ | Filtrage périmètre |
| Détail efficience ouvrage de tête | /efficiences/ouvrage/{type}/{id}/ | Vue agrégée tronçon par tronçon |

### 10.3 Composants du formulaire de calcul

- Sélecteur de méthode (infiltration, évaporation, les deux).
- Zone d'affichage des coefficients déduits du périmètre.
- Sélecteurs en cascade : ouvrage de tête → tronçons rattachés.
- Bouton « gérer les liaisons » pour créer ou modifier la relation séguia ↔ ouvrage.
- Indicateur visuel « DALOT » affiché conditionnellement.
- Tableau récapitulatif des tronçons rattachés.
- Bouton de lancement du calcul.
- Zone résultats à trois niveaux : tronçon, catégorie, global.

### 10.4 Code couleur des résultats

| Efficience | Code couleur |
|---|---|
| Supérieure à 80 % | Vert |
| Entre 50 % et 80 % | Orange |
| Inférieure à 50 % | Rouge |

---

## 11. LOTISSEMENT DES TÂCHES

### 11.1 Lot 0 — Adaptations du socle existant (estimé 1 jour)

| Tâche | Statut | Avancement |
|---|---|---|
| Ajout du champ ET0 sur Perimetre | À faire | 0 % |
| Ajout des champs efficience sur Seguias | À faire | 0 % |
| Renommage du lien menu base.html | À faire | 0 % |
| Migrations associées | À faire | 0 % |

### 11.2 Lot 1 — Fondations de l'application (estimé 3 jours)

| Tâche | Statut | Avancement |
|---|---|---|
| Création de l'application Django efficiences | À faire | 0 % |
| Configuration INSTALLED_APPS et URLs | À faire | 0 % |
| Modèle Efficience (résultats agrégés) | À faire | 0 % |
| Migrations initiales | À faire | 0 % |
| Enregistrement admin Django | À faire | 0 % |

### 11.3 Lot 2 — Services de calcul (estimé 5 jours)

| Tâche | Statut | Avancement |
|---|---|---|
| Service coefficients | À faire | 0 % |
| Service infiltration | À faire | 0 % |
| Service vaporisation (règle dalot) | À faire | 0 % |
| Service efficience tronçon | À faire | 0 % |
| Service agrégation (catégorie + global) | À faire | 0 % |
| Orchestrateur avec persistance | À faire | 0 % |
| Tests unitaires des formules | À faire | 0 % |

### 11.4 Lot 3 — Interfaces (estimé 6 jours)

| Tâche | Statut | Avancement |
|---|---|---|
| Template liste des périmètres | À faire | 0 % |
| Template formulaire de calcul | À faire | 0 % |
| Template gestion des liaisons | À faire | 0 % |
| Template historique | À faire | 0 % |
| Template détail ouvrage de tête | À faire | 0 % |
| Partiels AJAX (résultats trois niveaux, tronçons, liaisons) | À faire | 0 % |
| Feuille de style et JS | À faire | 0 % |
| Filtres template personnalisés | À faire | 0 % |

### 11.5 Lot 4 — Recette et mise en service (estimé 2 jours)

| Tâche | Statut | Avancement |
|---|---|---|
| Recette fonctionnelle | À faire | 0 % |
| Validation des bornes et cascade | À faire | 0 % |
| Documentation utilisateur | À faire | 0 % |
| Mise en production | À faire | 0 % |

**Charge totale estimée :** 17 jours-homme.

---

## 12. PLAN DE TESTS UNITAIRES

| Identifiant | Cas testé | Entrée | Sortie attendue |
|---|---|---|---|
| T01 | Coefficient C sol argileux | type_sol = argileux, non revêtu | 12 |
| T02 | Coefficient C revêtement béton | revêtement = béton | 1 |
| T03 | Périmètre mouillé | b=1,5 ; h=0,8 ; z=1 | 3,762 |
| T04 | Section mouillée | b=1,5 ; h=0,8 ; z=1 | 1,84 |
| T05 | Vitesse | Q=0,5 ; b=1,5 ; h=0,8 ; z=1 | 0,2717 |
| T06 | Règle dalot | type_ecoulement = dalot | Pi > 0 et Pv = 0 |
| T07 | Classification principale | Q = 1,5 m³/s | principal |
| T08 | Classification secondaire | Q = 0,5 m³/s | secondaire |
| T09 | Classification tertiaire | Q = 0,05 m³/s | tertiaire |
| T10 | Plafonnement efficience tronçon | Calcul théorique > 100 % | 100 % |
| T11 | Moyenne pondérée par débit | 2 tronçons (90 % à Q=1 ; 70 % à Q=3) | 75 % |
| T12 | Cascade trois catégories | E_p=90, E_s=80, E_t=70 | 50,4 % |
| T13 | Cascade avec catégorie absente | E_p=90, E_s absente, E_t=70 | 63 % |
| T14 | Persistance sur Seguias | Lancement calcul | Champs séguia mis à jour |
| T15 | Création entrée Efficience | Lancement calcul | Nouvel enregistrement Efficience |

---

## 13. PROCÉDURE D'INSTALLATION

### 13.1 Étapes prévues

1. Préparation : ajout du champ ET0 sur Perimetre et des champs efficience sur Seguias, génération et application des migrations correspondantes.
2. Création de l'application Django `efficiences` via la commande standard de gestion.
3. Déplacement dans le dossier `apps/` selon la convention du projet.
4. Inscription de l'application dans la liste `INSTALLED_APPS` du fichier `settings.py`.
5. Inclusion du fichier d'URLs dans le routeur principal sous le préfixe `/efficiences/`.
6. Création du modèle Efficience, génération et application des migrations.
7. Modification du lien menu dans `templates/base.html` (renommage en « Efficience des réseaux »).
8. Collecte des fichiers statiques pour l'environnement de production.

### 13.2 Vérifications post-installation

- L'application apparaît dans la liste des applications installées.
- Le lien « Efficience des réseaux » du menu est actif et pointe vers `/efficiences/`.
- Les URLs `/efficiences/` répondent correctement.
- Les templates sont chargés sans erreur.
- Les fichiers statiques sont accessibles via la racine `static`.
- Les calculs sur jeu de test retournent des valeurs cohérentes avec le plan de tests.
- L'entité Efficience reçoit bien un enregistrement après un calcul complet.
- Les champs efficience des séguias sont mis à jour à chaque calcul.

---

## 14. POINTS DE VIGILANCE

### 14.1 Conformité au socle existant

- Modifications limitées et tracées sur les applications en production (champs ajoutés uniquement, pas de modification destructive).
- Respecter la convention de nommage francophone de la plateforme.
- Conserver les fautes d'orthographe historiques baked dans les migrations (Besions_Ressources, efficiance, type_deguia, coordonnes_x) — toute correction nécessite un plan de migration explicite.

### 14.2 Cohérence métier

- Respecter la règle dalot impose Pv = 0.
- Veiller au plafonnement de l'efficience entre 0 % et 100 % à chaque niveau de la cascade.
- Aligner la classification sur les bornes de débit spécifiées (1,0 et 0,1 m³/s).
- S'assurer que la gestion des liaisons séguia ↔ ouvrage de tête respecte toujours le contexte du périmètre actif.

### 14.3 Données ET0

L'ajout du champ `et0_mm_jour` sur Périmètre est tranché et planifié au Lot 0. Une réflexion ultérieure pourra dériver automatiquement cette valeur depuis les stations climatiques de l'application Besions_Ressources, sans bloquer le développement de la V1.

### 14.4 Sauvegarde multi-niveaux

La double persistance — efficience tronçon dans Seguias + résultats agrégés dans Efficience — doit être transactionnelle. Toute opération de calcul doit garantir la cohérence des deux écritures.

---

## 15. ÉVOLUTIONS POSTÉRIEURES À LA V1

| Fonctionnalité | Bénéfice | Priorité |
|---|---|---|
| Dérivation automatique d'ET0 depuis stations climatiques | Réduction de la saisie manuelle | Haute |
| Graphiques d'évolution de l'efficience par séguia | Suivi temporel | Moyenne |
| Export PDF des rapports d'efficience | Diffusion administrative | Basse |
| API REST (Django REST Framework) | Interopérabilité | Haute |
| Système d'alertes par seuil | Anticipation des dégradations | Basse |
| Comparaison de scénarios (avant / après réhabilitation) | Aide à la décision investissement | Moyenne |
| Pondération alternative de l'agrégation (par longueur) | Approche métier complémentaire | Basse |

---

## 16. GLOSSAIRE

| Terme | Définition |
|---|---|
| Efficience | Pourcentage du débit initial qui n'est pas perdu entre l'amont et l'aval |
| Cascade d'efficiences | Produit en série des efficiences successives traversées par l'eau |
| ET0 | Évapotranspiration de référence exprimée en mm par jour |
| Dalot | Canal busé, enterré ou fermé, non exposé à l'air libre |
| Périmètre mouillé | Longueur de contact entre la lame d'eau et les parois du canal |
| Section mouillée | Surface de la section transversale occupée par l'eau |
| Séguia | Canal d'irrigation traditionnel (terminologie locale du Tafilalet) — assimilé à un tronçon |
| Ouvrage de tête | Ouvrage de captage en amont d'un réseau (seuil, prise, barrage, etc.) |
| Liaison séguia ↔ ouvrage de tête | Association N–N représentée par `SguiaAssocie_OuvrageTete` |
| Catégorie de canal | Principale, Secondaire ou Tertiaire selon le débit amont |

---

## 17. RÉFÉRENCES DOCUMENTAIRES

- Spécification technique du module Efficiences_Réseaux — version 1.1 du 21 mai 2026.
- Documentation interne CLAUDE.md du projet plateformeSIG.
- Référentiel des coefficients de Davis et Wilson — sources hydrauliques classiques.
- Modèle de données de l'application diagnostic — code source en production.
- Template de base `templates/base.html` — point d'entrée navigation.

---

**Document préparé pour conversion Word (Pandoc, Word Import ou copier-coller direct).**

**Auteur :** Équipe projet plateformeSIG
**Diffusion :** Comité de pilotage PFE / Encadrement académique / ORMVA
**Prochaine révision :** À l'issue du Lot 0 (adaptations du socle existant)

*Fin du document.*
