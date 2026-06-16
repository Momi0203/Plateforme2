"""
Management command : seed_plans_test
Génère trois plans PMH de test (2025 / 2026 / 2027) avec actions, calendriers et suivi.
Les données sont fictives et ne reflètent pas la réalité du terrain.

Usage :
    python manage.py seed_plans_test
    python manage.py seed_plans_test --reset
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Polygon
from django.core.management.base import BaseCommand

from carte.models import Commune, Province
from plan_action.models import (
    ActionPlan, CalendrierIntervention, PlanAmenagement,
    SuiviAvancement, TacheIntervention,
)

User = get_user_model()

# ── Durée (jours) des travaux principaux (T03) par type d'action ──────────────
_DUR = {
    'ACT-01': 30, 'ACT-02': 25, 'ACT-03': 25, 'ACT-04': 35,
    'ACT-05': 40, 'ACT-06': 20, 'ACT-07': 20, 'ACT-08': 15,
    'ACT-09': 20, 'ACT-10': 45, 'ACT-11': 30, 'ACT-12': 25,
    'ACT-13': 30, 'ACT-14': 15, 'ACT-15': 20, 'ACT-16': 25,
}


def _poly(x_off, y_off=0.0):
    """Carré unitaire décalé — géométrie fictive SRID 4326."""
    x, y = float(x_off), float(y_off)
    return Polygon(
        ((x, y), (x, y + 1.0), (x + 1.0, y + 1.0), (x + 1.0, y), (x, y)),
        srid=4326,
    )


def _get_or_create_province(nom, x_off):
    p, _ = Province.objects.get_or_create(
        nom_fr=nom,
        defaults=dict(
            nom_ar=f'إقليم {nom}',
            annee_refe=2014,
            population_totale=150000, population_urbaine=50000, population_rurale=100000,
            nombre_menages=30000, superficie_km2='8000.00', densite_hab_km2='18.75',
            taux_urbanisation_pct='33.33', taux_accroissement_pct='1.40',
            communes_urbaines=3, communes_rurales=12,
            station_meteo='STN-TEST', temp_moy_annuelle_c='18.5',
            precip_annuelle_mm='120.0', humidite_rel_moy_pct='45.0',
            et0_moy_journaliere_mm_j='5.50', et0_annuelle_mm='2007.5',
            geometrie=_poly(x_off),
        ),
    )
    return p


def _get_or_create_commune(province, nom, x_off):
    c, _ = Commune.objects.get_or_create(
        nom_fr=nom,
        defaults=dict(
            province=province,
            nom_ar=f'بلدية {nom}',
            type_commune='Rurale',
            population_totale=6000, nombre_menages=1200,
            superficie_km2='250.00', station_meteo='STN-SEED',
            temp_moy_annuelle_c='18.5', precip_annuelle_mm='120.0',
            humidite_rel_moy_pct='45.0', et0_moy_journaliere_mm_j='5.50',
            et0_annuelle_mm='2007.5',
            geometrie=_poly(x_off),
        ),
    )
    return c


def _make_tasks(cal, type_action, start_date, responsable, mode, author):
    """
    Crée les 5 tâches T01–T05 avec dépendances FS et suivi éventuel.

    mode :
        'en_cours'  → T01+T02 terminées (avec suivi), T03 en cours (avec suivi)
        'realise'   → toutes terminées (avec suivi 100 %)
        'brouillon' → toutes non démarrées, aucun suivi
    Retourne (nb_taches, nb_suivis).
    """
    dur = _DUR.get(type_action, 20)
    specs = [
        ('T01', 'Mobilisation et installations de chantier',      5,   'suivi_travaux'),
        ('T02', 'Travaux préparatoires (terrassement / implantation)', 10, 'suivi_travaux'),
        ('T03', 'Travaux principaux',                              dur, 'suivi_travaux'),
        ('T04', 'Contrôle qualité et essais',                     5,   'suivi_travaux'),
        ('T05', 'Réception provisoire et clôture administrative', 3,   'suivi_administratif'),
    ]

    taches = {}
    current = start_date
    for code, nom, duree, type_suivi in specs:
        debut = current
        fin   = debut + timedelta(days=duree - 1)
        if mode == 'en_cours':
            statut = ('terminee'     if code in ('T01', 'T02')
                      else 'en_cours' if code == 'T03'
                      else 'non_demarree')
        elif mode == 'realise':
            statut = 'terminee'
        else:
            statut = 'non_demarree'

        taches[code] = TacheIntervention.objects.create(
            calendrier=cal, code_tache=code, nom_tache=nom,
            date_debut_prevue=debut, date_fin_prevue=fin, duree_prevue=duree,
            responsable=responsable, type_suivi=type_suivi, statut_tache=statut,
        )
        current = fin + timedelta(days=1)

    # Dépendances Finish-to-Start
    for pred, succ in (('T01', 'T02'), ('T02', 'T03'), ('T03', 'T04'), ('T04', 'T05')):
        taches[succ].taches_anterieures.add(taches[pred])

    # ── Suivi d'avancement ─────────────────────────────────────────────────────
    n_suivis = 0
    if mode == 'en_cours':
        suivis = [
            ('T01', 50,  'conforme', 3,  'Mobilisation bien engagée.'),
            ('T01', 100, 'termine',  6,  'Mobilisation achevée.'),
            ('T02', 60,  'conforme', 12, 'Terrassement avancé.'),
            ('T02', 100, 'termine',  17, 'Travaux préparatoires réceptionnés.'),
            ('T03', 35,  'conforme', 32, 'Travaux principaux en cours — 35 %.'),
            ('T03', 65,  'conforme', 47, 'Travaux principaux en cours — 65 %.'),
        ]
        for code, pct, etat, delta, comment in suivis:
            SuiviAvancement.objects.create(
                tache=taches[code], auteur=author,
                date_rapport=start_date + timedelta(days=delta),
                avancement_pct=pct, etat_bloc=etat, commentaire=comment,
            )
            n_suivis += 1

    elif mode == 'realise':
        for t in taches.values():
            SuiviAvancement.objects.create(
                tache=t, auteur=author,
                date_rapport=t.date_fin_prevue,
                avancement_pct=100, etat_bloc='termine',
                commentaire='Tâche réceptionnée et clôturée.',
            )
            n_suivis += 1

    return len(taches), n_suivis


def _cal_end(start_date, type_action):
    """Date de fin du calendrier = somme des durées T01–T05."""
    total = 5 + 10 + _DUR.get(type_action, 20) + 5 + 3
    return start_date + timedelta(days=total - 1)


# ── Commande ──────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Génère les scénarios de test PMH pour les plans 2025, 2026 et 2027.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Supprime les plans 2025/2026/2027 avant de les recréer.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            n, _ = PlanAmenagement.objects.filter(annee__in=[2025, 2026, 2027]).delete()
            self.stdout.write(self.style.WARNING(f'  {n} plan(s) test supprime(s) (--reset).'))

        # Trouver un utilisateur admin
        admin = (
            User.objects.filter(is_superuser=True).first()
            or User.objects.filter(role='administrateur').first()
        )
        if not admin:
            self.stderr.write(self.style.ERROR(
                'Aucun superuser trouve. Lancez : python manage.py createsuperuser'
            ))
            return

        operateur = User.objects.filter(role='operateur').first() or admin

        communes = self._get_communes()

        totals = dict(plans=0, actions=0, calendriers=0, taches=0, suivis=0)
        self._plan_2025(admin, operateur, communes, totals)
        self._plan_2026(admin, operateur, communes, totals)
        self._plan_2027(admin, operateur, communes, totals)

        self.stdout.write(self.style.SUCCESS(
            f"\n  Resultat : {totals['plans']} plan(s) cree(s), "
            f"{totals['actions']} action(s), "
            f"{totals['calendriers']} calendrier(s), "
            f"{totals['taches']} tache(s), "
            f"{totals['suivis']} rapport(s) de suivi."
        ))

    # ── Communes ───────────────────────────────────────────────────────────────

    def _get_communes(self):
        communes = list(Commune.objects.select_related('province').all()[:10])
        if len(communes) >= 5:
            self.stdout.write(f'  Utilisation de {min(len(communes), 5)} commune(s) existante(s).')
            return communes[:5]

        self.stdout.write(self.style.WARNING('  Moins de 5 communes en base — creation de communes fictives.'))
        prov_m = _get_or_create_province('Province Test Midelt',      0.0)
        prov_e = _get_or_create_province('Province Test Errachidia', 20.0)
        seed_communes = [
            ('Commune Test Aghbalou',  prov_m,  2.0),
            ('Commune Test Ouaoumana', prov_m,  4.0),
            ('Commune Test Tarhbalt',  prov_m,  6.0),
            ('Commune Test Goulmima',  prov_e,  8.0),
            ('Commune Test Tinejdad',  prov_e, 10.0),
        ]
        result = []
        for nom, prov, x in seed_communes:
            result.append(_get_or_create_commune(prov, nom, x))
        return result

    # ── Plan 2025 — Publié / En cours ─────────────────────────────────────────

    def _plan_2025(self, admin, operateur, C, totals):
        if PlanAmenagement.objects.filter(annee=2025).exists():
            self.stdout.write('  Plan 2025 deja existant => ignore (--reset pour recreer).')
            return

        plan = PlanAmenagement.objects.create(
            annee=2025,
            titre='Programme PMH Tafilalet — Exercice 2025',
            budget_total='12000000.00',
            source_financement='budget_etat',
            statut='publie',
            description='Scenario de test — donnees fictives.',
            cree_par=admin,
        )
        totals['plans'] += 1

        # (comm_idx, type_action, budget, priorite, statut_action, mode_cal)
        # mode_cal : 'en_cours' | 'realise' | None (pas de calendrier)
        actions_spec = [
            (0, 'ACT-01', '1200000.00', 1, 'en_cours',  'en_cours'),
            (0, 'ACT-03', '900000.00',  1, 'en_cours',  'en_cours'),
            (1, 'ACT-04', '800000.00',  1, 'realise',   'realise'),
            (1, 'ACT-07', '600000.00',  2, 'realise',   'realise'),
            (2, 'ACT-01', '1500000.00', 1, 'en_cours',  'en_cours'),
            (2, 'ACT-16', '1100000.00', 1, 'en_cours',  'en_cours'),
            (3, 'ACT-08', '700000.00',  2, 'programme', None),
            (3, 'ACT-10', '1800000.00', 2, 'programme', None),
            (4, 'ACT-09', '900000.00',  3, 'programme', None),
            (4, 'ACT-14', '500000.00',  3, 'programme', None),
        ]

        start = date(2025, 3, 1)
        for ci, ta, budget, prio, statut, mode_cal in actions_spec:
            action = ActionPlan.objects.create(
                plan=plan, commune=C[ci], type_action=ta,
                description=f'Travaux {ta} a {C[ci].nom_fr} (test 2025)',
                budget_prevu=budget, priorite=prio, statut=statut,
            )
            totals['actions'] += 1

            if mode_cal:
                cal = CalendrierIntervention.objects.create(
                    action=action,
                    date_debut_prevue=start,
                    date_fin_prevue=_cal_end(start, ta),
                    mode_realisation='marche_public',
                    chef_projet=admin,
                    statut_calendrier='valide',
                    valide_par=admin,
                )
                totals['calendriers'] += 1
                nt, ns = _make_tasks(cal, ta, start, operateur, mode_cal, admin)
                totals['taches'] += nt
                totals['suivis'] += ns

        self.stdout.write(
            f'  [OK] Plan 2025 (publie) — '
            f'{len(actions_spec)} actions, '
            f'6 calendriers valides, suivi partiel.'
        )

    # ── Plan 2026 — En préparation ─────────────────────────────────────────────

    def _plan_2026(self, admin, operateur, C, totals):
        if PlanAmenagement.objects.filter(annee=2026).exists():
            self.stdout.write('  Plan 2026 deja existant => ignore.')
            return

        plan = PlanAmenagement.objects.create(
            annee=2026,
            titre='Programme PMH Tafilalet — Exercice 2026',
            budget_total='15000000.00',
            source_financement='budget_etat',
            statut='en_preparation',
            description='Scenario de test — donnees fictives.',
            cree_par=admin,
        )
        totals['plans'] += 1

        # (comm_idx, type_action, budget, priorite, has_cal)
        actions_spec = [
            (0, 'ACT-02', '2000000.00', 1, True),
            (1, 'ACT-05', '3500000.00', 1, True),
            (1, 'ACT-16', '1200000.00', 1, True),
            (2, 'ACT-01', '1400000.00', 2, True),
            (2, 'ACT-13', '900000.00',  1, True),
            (3, 'ACT-04', '1000000.00', 2, False),
            (3, 'ACT-10', '2200000.00', 2, False),
            (4, 'ACT-11', '800000.00',  3, False),
            (4, 'ACT-06', '700000.00',  3, False),
            (0, 'ACT-14', '1300000.00', 1, False),
        ]

        start = date(2026, 3, 1)
        for ci, ta, budget, prio, has_cal in actions_spec:
            action = ActionPlan.objects.create(
                plan=plan, commune=C[ci], type_action=ta,
                description=f'Travaux {ta} a {C[ci].nom_fr} (test 2026)',
                budget_prevu=budget, priorite=prio, statut='programme',
            )
            totals['actions'] += 1

            if has_cal:
                cal = CalendrierIntervention.objects.create(
                    action=action,
                    date_debut_prevue=start,
                    date_fin_prevue=_cal_end(start, ta),
                    mode_realisation='marche_public',
                    chef_projet=admin,
                    statut_calendrier='brouillon',
                )
                totals['calendriers'] += 1
                nt, ns = _make_tasks(cal, ta, start, operateur, 'brouillon', admin)
                totals['taches'] += nt
                totals['suivis'] += ns

        self.stdout.write(
            f'  [OK] Plan 2026 (en preparation) — '
            f'{len(actions_spec)} actions, '
            f'5 calendriers brouillon, aucun suivi.'
        )

    # ── Plan 2027 — Prospectif ─────────────────────────────────────────────────

    def _plan_2027(self, admin, operateur, C, totals):
        if PlanAmenagement.objects.filter(annee=2027).exists():
            self.stdout.write('  Plan 2027 deja existant => ignore.')
            return

        plan = PlanAmenagement.objects.create(
            annee=2027,
            titre='Programme PMH Tafilalet — Exercice 2027 (prospectif)',
            budget_total='18000000.00',
            source_financement='partenariat',
            statut='en_preparation',
            description='Scenario de test prospectif — donnees fictives, aucun calendrier.',
            cree_par=admin,
        )
        totals['plans'] += 1

        actions_spec = [
            (0, 'ACT-10', '3500000.00', 1),
            (1, 'ACT-10', '3000000.00', 1),
            (2, 'ACT-01', '1800000.00', 1),
            (2, 'ACT-16', '1500000.00', 1),
            (3, 'ACT-05', '2500000.00', 1),
            (3, 'ACT-04', '1000000.00', 2),
            (4, 'ACT-07', '800000.00',  2),
            (4, 'ACT-09', '700000.00',  2),
            (0, 'ACT-12', '1200000.00', 3),
            (1, 'ACT-14', '2000000.00', 1),
        ]

        for ci, ta, budget, prio in actions_spec:
            ActionPlan.objects.create(
                plan=plan, commune=C[ci], type_action=ta,
                description=f'Travaux {ta} a {C[ci].nom_fr} (test 2027)',
                budget_prevu=budget, priorite=prio, statut='programme',
            )
            totals['actions'] += 1

        self.stdout.write(
            f'  [OK] Plan 2027 (prospectif) — '
            f'{len(actions_spec)} actions, aucun calendrier.'
        )
