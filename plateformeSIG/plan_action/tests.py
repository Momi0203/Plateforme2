"""
Tests unitaires et d'intégration — module plan_action.
Couvre les scénarios SC-01..SC-10 du cahier des charges.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Polygon
from django.test import Client, TestCase
from django.urls import reverse

from django.core.files.uploadedfile import SimpleUploadedFile

from carte.models import Commune, Province
from plan_action.models import (
    ActionPlan,
    CalendrierIntervention,
    PlanAmenagement,
    PieceJustificative,
    SuiviAvancement,
    TacheIntervention,
)
from plan_action.utils import compute_cpm, has_cycle

# Minimal 1×1 JPEG bytes for upload tests
_JPEG_BYTES = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
    b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
    b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
    b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1edL\t\r'
    b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
    b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00'
    b'\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
    b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00'
    b'\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07'
    b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd0\xff\xd9'
)

User = get_user_model()

_GEO = Polygon(
    ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)),
    srid=4326,
)
_TODAY = date.today()


# ─── Fixtures partagées ───────────────────────────────────────────────────────

def _make_province(suffix=''):
    return Province.objects.create(
        nom_fr=f'Province {suffix}', nom_ar='مقاطعة', annee_refe=2024,
        population_totale=10000, population_urbaine=5000, population_rurale=5000,
        nombre_menages=2000, superficie_km2='500.00', densite_hab_km2='20.00',
        taux_urbanisation_pct='50.00', taux_accroissement_pct='1.50',
        communes_urbaines=2, communes_rurales=5, station_meteo='TST',
        temp_moy_annuelle_c='18.5', precip_annuelle_mm='200.0',
        humidite_rel_moy_pct='40.0', et0_moy_journaliere_mm_j='5.00',
        et0_annuelle_mm='1825.0', geometrie=_GEO,
    )


def _make_commune(province, nom):
    return Commune.objects.create(
        province=province, nom_fr=nom, nom_ar='بلدية',
        type_commune='Rurale', population_totale=3000, nombre_menages=600,
        station_meteo='TST', temp_moy_annuelle_c='18.5',
        precip_annuelle_mm='200.0', humidite_rel_moy_pct='40.0',
        et0_moy_journaliere_mm_j='5.00', et0_annuelle_mm='1825.0',
        geometrie=_GEO,
    )


# ─── Tests utilitaires (SC-03) ────────────────────────────────────────────────

class HasCycleTests(TestCase):
    """Tests unitaires (sans BD) pour has_cycle — SC-03."""

    def test_no_cycle_linear(self):
        self.assertFalse(has_cycle([(0, 1), (1, 2), (2, 3)], {0, 1, 2, 3}))

    def test_no_cycle_diamond(self):
        self.assertFalse(has_cycle([(0, 1), (0, 2), (1, 3), (2, 3)], {0, 1, 2, 3}))

    def test_simple_cycle(self):
        # SC-03 : T2→T3 et T3→T2
        self.assertTrue(has_cycle([(1, 2), (2, 1)], {1, 2}))

    def test_triangle_cycle(self):
        self.assertTrue(has_cycle([(0, 1), (1, 2), (2, 0)], {0, 1, 2}))

    def test_self_loop(self):
        self.assertTrue(has_cycle([(0, 0)], {0}))

    def test_empty(self):
        self.assertFalse(has_cycle([], set()))

    def test_disconnected_no_cycle(self):
        self.assertFalse(has_cycle([(0, 1), (2, 3)], {0, 1, 2, 3}))


# ─── Tests CPM (SC-05) ────────────────────────────────────────────────────────

class CPMTests(TestCase):
    """Tests calcul CPM — SC-05 (chemin critique)."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='admin_cpm', password='pass', role='administrateur',
        )
        prov = _make_province('CPM')
        comm = _make_commune(prov, 'Commune CPM')
        plan = PlanAmenagement.objects.create(
            annee=2099, titre='CPM Plan', budget_total='100000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=cls.admin,
        )
        action = ActionPlan.objects.create(
            plan=plan, commune=comm, type_action='ACT-01',
            description='CPM', budget_prevu='100000.00',
            priorite=1, statut='programme',
        )
        cls.cal = CalendrierIntervention.objects.create(
            action=action,
            date_debut_prevue=_TODAY,
            date_fin_prevue=_TODAY + timedelta(days=40),
            mode_realisation='regie',
            chef_projet=cls.admin,
            statut_calendrier='brouillon',
        )
        # T1(10j), T2(20j), T3(15j) dépend T1 et T2
        # Chemin critique : T2 → T3 (durée 35j)
        cls.t1 = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='T01', nom_tache='Tâche 1',
            date_debut_prevue=_TODAY, date_fin_prevue=_TODAY + timedelta(days=10),
            duree_prevue=10, responsable=cls.admin,
            type_suivi='suivi_travaux', statut_tache='non_demarree',
        )
        cls.t2 = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='T02', nom_tache='Tâche 2',
            date_debut_prevue=_TODAY, date_fin_prevue=_TODAY + timedelta(days=20),
            duree_prevue=20, responsable=cls.admin,
            type_suivi='suivi_travaux', statut_tache='non_demarree',
        )
        cls.t3 = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='T03', nom_tache='Tâche 3',
            date_debut_prevue=_TODAY + timedelta(days=20),
            date_fin_prevue=_TODAY + timedelta(days=35),
            duree_prevue=15, responsable=cls.admin,
            type_suivi='suivi_travaux', statut_tache='non_demarree',
        )
        cls.t3.taches_anterieures.set([cls.t1, cls.t2])

    def _cpm(self):
        return compute_cpm(self.cal.taches.all())

    def test_project_duration_35(self):
        result = self._cpm()
        self.assertEqual(max(v['EF'] for v in result.values()), 35)

    def test_t2_critical(self):
        result = self._cpm()
        self.assertTrue(result[self.t2.pk]['is_critical'])

    def test_t3_critical(self):
        result = self._cpm()
        self.assertTrue(result[self.t3.pk]['is_critical'])

    def test_t1_not_critical_marge_10(self):
        result = self._cpm()
        self.assertFalse(result[self.t1.pk]['is_critical'])
        self.assertEqual(result[self.t1.pk]['marge'], 10)

    def test_es_ef_t3(self):
        result = self._cpm()
        self.assertEqual(result[self.t3.pk]['ES'], 20)
        self.assertEqual(result[self.t3.pk]['EF'], 35)

    def test_pert_data_endpoint_ok(self):
        """Endpoint /pert/data/ — SC-05."""
        c = Client()
        c.login(username='admin_cpm', password='pass')
        url = reverse('plan_action:pert_data', kwargs={'action_pk': self.cal.action.pk})
        r = c.get(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['nb_taches'], 3)
        self.assertEqual(data['nb_critiques'], 2)
        self.assertEqual(data['project_duration'], 35)


# ─── Tests de permissions (SEC-01..SEC-04, SC-04, SC-07, SC-09) ──────────────

class PermissionTests(TestCase):
    """
    Tests de la matrice des droits : visiteur / opérateur / éditeur / admin.
    Couvre SC-04, SC-07, SC-09 et les exigences SEC-01..SEC-04.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='adm', password='pass', role='administrateur',
        )
        cls.operateur = User.objects.create_user(
            username='oper', password='pass', role='operateur',
        )
        cls.visiteur = User.objects.create_user(
            username='visit', password='pass', role='visiteur',
        )
        cls.editeur = User.objects.create_user(
            username='edit', password='pass', role='editeur',
        )

        prov = _make_province('PERM')
        cls.commune = _make_commune(prov, 'Commune Perm')

        cls.plan = PlanAmenagement.objects.create(
            annee=2060, titre='Plan Perm', budget_total='500000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=cls.admin,
        )
        cls.action = ActionPlan.objects.create(
            plan=cls.plan, commune=cls.commune, type_action='ACT-01',
            description='Test', budget_prevu='100000.00',
            priorite=2, statut='programme',
        )
        cls.cal = CalendrierIntervention.objects.create(
            action=cls.action,
            date_debut_prevue=_TODAY,
            date_fin_prevue=_TODAY + timedelta(days=30),
            mode_realisation='regie',
            chef_projet=cls.operateur,
            statut_calendrier='brouillon',
        )
        cls.tache_oper = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='P01', nom_tache='Tâche opérateur',
            date_debut_prevue=_TODAY, date_fin_prevue=_TODAY + timedelta(days=10),
            duree_prevue=10, responsable=cls.operateur,
            type_suivi='suivi_travaux', statut_tache='non_demarree',
        )
        cls.tache_edit = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='P02', nom_tache='Tâche éditeur',
            date_debut_prevue=_TODAY + timedelta(days=10),
            date_fin_prevue=_TODAY + timedelta(days=20),
            duree_prevue=10, responsable=cls.editeur,
            type_suivi='suivi_travaux', statut_tache='non_demarree',
        )

    # ── SEC-01 : @login_required sur toutes les vues /plan/ ──────────────────

    def test_sec01_anonymous_plan_list_redirect(self):
        r = Client().get(reverse('plan_action:plan_list'))
        self.assertEqual(r.status_code, 302)

    def test_sec01_anonymous_plan_create_redirect_to_login(self):
        """SC-09 (partiel) : non connecté → redirect vers page de connexion."""
        r = Client().get(reverse('plan_action:plan_create'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('next=/plan/creer/', r.url)

    # ── SC-11/SC-12 : visiteur authentifié → 403 sur toute lecture /plan/ ──────

    def test_visiteur_read_plan_list_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(c.get(reverse('plan_action:plan_list')).status_code, 403)

    def test_visiteur_read_plan_detail_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:plan_detail', kwargs={'pk': self.plan.pk})).status_code,
            403,
        )

    def test_visiteur_read_gantt_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:calendrier_gantt', kwargs={'action_pk': self.action.pk})).status_code,
            403,
        )

    def test_visiteur_read_pert_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:calendrier_pert', kwargs={'action_pk': self.action.pk})).status_code,
            403,
        )

    def test_visiteur_read_suivi_global_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(c.get(reverse('plan_action:suivi_global')).status_code, 403)

    def test_visiteur_read_suivi_dashboard_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:suivi_dashboard', kwargs={'action_pk': self.action.pk})).status_code,
            403,
        )

    # ── Lecture autorisée pour opérateur et éditeur ──────────────────────────

    def test_operateur_read_plan_list_200(self):
        c = Client()
        c.login(username='oper', password='pass')
        self.assertEqual(c.get(reverse('plan_action:plan_list')).status_code, 200)

    def test_editeur_read_plan_list_200(self):
        c = Client()
        c.login(username='edit', password='pass')
        self.assertEqual(c.get(reverse('plan_action:plan_list')).status_code, 200)

    def test_editeur_read_gantt_200(self):
        c = Client()
        c.login(username='edit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:calendrier_gantt', kwargs={'action_pk': self.action.pk})).status_code,
            200,
        )

    def test_editeur_read_pert_200(self):
        c = Client()
        c.login(username='edit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:calendrier_pert', kwargs={'action_pk': self.action.pk})).status_code,
            200,
        )

    # ── SC-09 : visiteur connecté → 403 sur mutations A1 ────────────────────

    def test_sc09_visiteur_plan_create_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(c.get(reverse('plan_action:plan_create')).status_code, 403)

    def test_sc09_visiteur_plan_update_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:plan_update', kwargs={'pk': self.plan.pk})).status_code,
            403,
        )

    def test_sc09_visiteur_action_create_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:action_create', kwargs={'plan_pk': self.plan.pk})).status_code,
            403,
        )

    def test_sc09_editeur_plan_create_403(self):
        """Éditeur ne peut pas créer un plan (A1 write : ✗ éditeur)."""
        c = Client()
        c.login(username='edit', password='pass')
        self.assertEqual(c.get(reverse('plan_action:plan_create')).status_code, 403)

    def test_operateur_plan_create_ok(self):
        c = Client()
        c.login(username='oper', password='pass')
        self.assertEqual(c.get(reverse('plan_action:plan_create')).status_code, 200)

    # ── A1 suppression — admin seulement ─────────────────────────────────────

    def test_visiteur_plan_delete_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:plan_delete', kwargs={'pk': self.plan.pk})).status_code,
            403,
        )

    def test_operateur_plan_delete_403(self):
        c = Client()
        c.login(username='oper', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:plan_delete', kwargs={'pk': self.plan.pk})).status_code,
            403,
        )

    def test_admin_plan_delete_ok(self):
        c = Client()
        c.login(username='adm', password='pass')
        self.assertEqual(
            c.get(reverse('plan_action:plan_delete', kwargs={'pk': self.plan.pk})).status_code,
            200,
        )

    # ── SC-04 : validation calendrier — admin seulement ─────────────────────

    def test_sc04_operateur_valider_403(self):
        c = Client()
        c.login(username='oper', password='pass')
        url = reverse('plan_action:valider_calendrier', kwargs={'action_pk': self.action.pk})
        self.assertEqual(c.post(url).status_code, 403)

    def test_sc04_visiteur_valider_403(self):
        c = Client()
        c.login(username='visit', password='pass')
        url = reverse('plan_action:valider_calendrier', kwargs={'action_pk': self.action.pk})
        self.assertEqual(c.post(url).status_code, 403)

    def test_sc04_admin_valider_sets_statut(self):
        c = Client()
        c.login(username='adm', password='pass')
        url = reverse('plan_action:valider_calendrier', kwargs={'action_pk': self.action.pk})
        c.post(url)
        self.cal.refresh_from_db()
        self.assertEqual(self.cal.statut_calendrier, 'valide')
        # reset
        self.cal.statut_calendrier = 'brouillon'
        self.cal.save()

    def test_sc04_operateur_cannot_edit_validated(self):
        """SEC-04 : opérateur redirigé si calendrier validé."""
        self.cal.statut_calendrier = 'valide'
        self.cal.save()
        c = Client()
        c.login(username='oper', password='pass')
        r = c.get(reverse('plan_action:calendrier_form', kwargs={'action_pk': self.action.pk}))
        self.assertEqual(r.status_code, 302)
        self.cal.statut_calendrier = 'brouillon'
        self.cal.save()

    def test_sc04_admin_can_edit_validated(self):
        """Admin peut modifier un calendrier validé."""
        self.cal.statut_calendrier = 'valide'
        self.cal.save()
        c = Client()
        c.login(username='adm', password='pass')
        r = c.get(reverse('plan_action:calendrier_form', kwargs={'action_pk': self.action.pk}))
        self.assertEqual(r.status_code, 200)
        self.cal.statut_calendrier = 'brouillon'
        self.cal.save()

    # ── SC-14 / SC-15 : éditeur bloqué sur écriture A2 ─────────────────────

    def test_sc14_editeur_calendrier_form_403(self):
        """SC-14 : éditeur ne peut pas créer/modifier un calendrier."""
        c = Client()
        c.login(username='edit', password='pass')
        url = reverse('plan_action:calendrier_form', kwargs={'action_pk': self.action.pk})
        self.assertEqual(c.get(url).status_code, 403)

    def test_sc15_editeur_valider_calendrier_403(self):
        """SC-15 : éditeur ne peut pas valider un calendrier."""
        c = Client()
        c.login(username='edit', password='pass')
        url = reverse('plan_action:valider_calendrier', kwargs={'action_pk': self.action.pk})
        self.assertEqual(c.post(url).status_code, 403)

    # ── SC-07 : suivi — contrôle responsable (SEC-02) ────────────────────────

    def test_sc07_visiteur_suivi_403(self):
        """Visiteur → 403 (require_role bloque avant le check responsable)."""
        c = Client()
        c.login(username='visit', password='pass')
        url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache_oper.pk})
        self.assertEqual(c.get(url).status_code, 403)

    def test_sc07_operateur_not_responsable_403(self):
        """Opérateur authentifié mais pas responsable de tache_edit → 403."""
        c = Client()
        c.login(username='oper', password='pass')
        url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache_edit.pk})
        self.assertEqual(c.get(url).status_code, 403)

    def test_sc07_editeur_not_responsable_403(self):
        """Éditeur authentifié mais pas responsable de tache_oper → 403."""
        c = Client()
        c.login(username='edit', password='pass')
        url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache_oper.pk})
        self.assertEqual(c.get(url).status_code, 403)

    def test_sc07_responsable_operateur_ok(self):
        """Opérateur responsable de sa tâche → 200."""
        c = Client()
        c.login(username='oper', password='pass')
        url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache_oper.pk})
        self.assertEqual(c.get(url).status_code, 200)

    def test_sc07_responsable_editeur_ok(self):
        """Éditeur responsable de sa tâche → 200."""
        c = Client()
        c.login(username='edit', password='pass')
        url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache_edit.pk})
        self.assertEqual(c.get(url).status_code, 200)

    def test_sc07_admin_any_tache_ok(self):
        """Admin (superuser) passe le check responsable."""
        c = Client()
        c.login(username='adm', password='pass')
        url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache_oper.pk})
        self.assertEqual(c.get(url).status_code, 200)


# ─── Tests CRUD plan (SC-01) et export Excel (SC-10) ─────────────────────────

class PlanActionCRUDTests(TestCase):
    """SC-01 : création plan multi-communes, SC-10 : export Excel."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='adm2', password='pass', role='administrateur',
        )
        prov = _make_province('CRUD')
        cls.communes = [_make_commune(prov, f'Commune CRUD {i}') for i in range(3)]

    def test_sc01_plan_creation_visible_in_list(self):
        """SC-01 : plan créé → visible dans la liste."""
        plan = PlanAmenagement.objects.create(
            annee=2071, titre='Plan SC01', budget_total='500000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=self.admin,
        )
        for i in range(5):
            ActionPlan.objects.create(
                plan=plan, commune=self.communes[i % 3], type_action='ACT-01',
                description=f'Action {i}', budget_prevu='50000.00',
                priorite=2, statut='programme',
            )
        c = Client()
        c.login(username='adm2', password='pass')
        r = c.get(reverse('plan_action:plan_list'))
        self.assertContains(r, 'Plan SC01')

    def test_sc01_taux_zero_for_new_plan(self):
        """SC-01 : taux réalisation = 0 % quand aucune action réalisée."""
        plan = PlanAmenagement.objects.create(
            annee=2072, titre='Plan Taux 0', budget_total='100000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=self.admin,
        )
        ActionPlan.objects.create(
            plan=plan, commune=self.communes[0], type_action='ACT-02',
            description='Test', budget_prevu='100000.00', priorite=1,
            statut='programme',
        )
        self.assertEqual(plan.taux_realisation(), 0)

    def test_sc01_taux_100_when_all_realise(self):
        """Taux monte à 100 % quand toutes les actions sont réalisées."""
        plan = PlanAmenagement.objects.create(
            annee=2073, titre='Plan Taux 100', budget_total='100000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=self.admin,
        )
        action = ActionPlan.objects.create(
            plan=plan, commune=self.communes[0], type_action='ACT-03',
            description='Test', budget_prevu='100000.00', priorite=1,
            statut='programme',
        )
        self.assertEqual(plan.taux_realisation(), 0)
        action.statut = 'realise'
        action.save()
        self.assertEqual(plan.taux_realisation(), 100)

    def test_sc01_filter_by_year(self):
        """SC-01 : plan filtrable par année."""
        PlanAmenagement.objects.create(
            annee=2074, titre='Filtrable', budget_total='100000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=self.admin,
        )
        c = Client()
        c.login(username='adm2', password='pass')
        r = c.get(reverse('plan_action:plan_list') + '?annee=2074')
        self.assertContains(r, 'Filtrable')

    def test_sc10_export_xlsx_content_type(self):
        """SC-10 : export retourne bien un fichier .xlsx."""
        plan = PlanAmenagement.objects.create(
            annee=2075, titre='Export SC10', budget_total='200000.00',
            source_financement='budget_etat', statut='publie',
            cree_par=self.admin,
        )
        ActionPlan.objects.create(
            plan=plan, commune=self.communes[0], type_action='ACT-04',
            description='Export', budget_prevu='50000.00',
            priorite=1, statut='programme',
        )
        c = Client()
        c.login(username='adm2', password='pass')
        r = c.get(reverse('plan_action:export_plan_excel', kwargs={'pk': plan.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('.xlsx', r['Content-Disposition'])

    def test_sc10_export_operateur_ok(self):
        """Export Excel accessible aux agents connectés (opérateur/éditeur) — visiteur bloqué."""
        plan = PlanAmenagement.objects.create(
            annee=2076, titre='Export Operateur', budget_total='100000.00',
            source_financement='budget_etat', statut='publie',
            cree_par=self.admin,
        )
        ActionPlan.objects.create(
            plan=plan, commune=self.communes[0], type_action='ACT-05',
            description='Test', budget_prevu='50000.00',
            priorite=1, statut='programme',
        )
        operateur = User.objects.create_user(username='oper_exp', password='pass', role='operateur')
        c = Client()
        c.login(username='oper_exp', password='pass')
        r = c.get(reverse('plan_action:export_plan_excel', kwargs={'pk': plan.pk}))
        self.assertEqual(r.status_code, 200)

    def test_sc10_export_visiteur_403(self):
        """Export Excel interdit au visiteur (matrice S13)."""
        plan = PlanAmenagement.objects.create(
            annee=2077, titre='Export Visiteur 403', budget_total='100000.00',
            source_financement='budget_etat', statut='publie',
            cree_par=self.admin,
        )
        visiteur = User.objects.create_user(username='vis_exp', password='pass', role='visiteur')
        c = Client()
        c.login(username='vis_exp', password='pass')
        r = c.get(reverse('plan_action:export_plan_excel', kwargs={'pk': plan.pk}))
        self.assertEqual(r.status_code, 403)


# ─── Tests Gantt dépendances + retard (SC-02, SC-08 gantt) ───────────────────

class GanttDependencyTests(TestCase):
    """
    SC-02 : gantt_data retourne les liens FS (T3 dépend T1+T2).
    SC-08 (gantt) : tâche en retard → classe 'gantt-retard' dans custom_class.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='adm_gd', password='pass', role='administrateur',
        )
        prov = _make_province('GD')
        comm = _make_commune(prov, 'Commune GD')
        plan = PlanAmenagement.objects.create(
            annee=2085, titre='Plan GD', budget_total='100000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=cls.admin,
        )
        cls.action = ActionPlan.objects.create(
            plan=plan, commune=comm, type_action='ACT-01',
            description='GD', budget_prevu='100000.00', priorite=1,
            statut='programme',
        )
        cls.cal = CalendrierIntervention.objects.create(
            action=cls.action,
            date_debut_prevue=_TODAY - timedelta(days=30),
            date_fin_prevue=_TODAY + timedelta(days=30),
            mode_realisation='regie',
            chef_projet=cls.admin,
            statut_calendrier='valide',
        )
        # SC-02 : T1(10j) + T2(20j) → T3(15j)
        cls.t1 = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='T01', nom_tache='T1',
            date_debut_prevue=_TODAY - timedelta(days=30),
            date_fin_prevue=_TODAY - timedelta(days=20),
            duree_prevue=10, responsable=cls.admin,
            type_suivi='suivi_travaux', statut_tache='terminee',
        )
        cls.t2 = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='T02', nom_tache='T2',
            date_debut_prevue=_TODAY - timedelta(days=30),
            date_fin_prevue=_TODAY - timedelta(days=10),
            duree_prevue=20, responsable=cls.admin,
            type_suivi='suivi_travaux', statut_tache='terminee',
        )
        cls.t3 = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='T03', nom_tache='T3',
            date_debut_prevue=_TODAY - timedelta(days=10),
            date_fin_prevue=_TODAY + timedelta(days=5),
            duree_prevue=15, responsable=cls.admin,
            type_suivi='suivi_travaux', statut_tache='en_cours',
        )
        cls.t3.taches_anterieures.set([cls.t1, cls.t2])

        # SC-08 : tâche en retard (délai dépassé, non terminée)
        cls.t_retard = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='T04', nom_tache='T retard',
            date_debut_prevue=_TODAY - timedelta(days=20),
            date_fin_prevue=_TODAY - timedelta(days=5),
            duree_prevue=15, responsable=cls.admin,
            type_suivi='suivi_travaux', statut_tache='non_demarree',
        )

    def _gantt_tasks(self):
        c = Client()
        c.login(username='adm_gd', password='pass')
        url = reverse('plan_action:gantt_data', kwargs={'action_pk': self.action.pk})
        return c.get(url).json()['tasks']

    def test_sc02_gantt_data_status_200(self):
        c = Client()
        c.login(username='adm_gd', password='pass')
        r = c.get(reverse('plan_action:gantt_data', kwargs={'action_pk': self.action.pk}))
        self.assertEqual(r.status_code, 200)

    def test_sc02_gantt_t3_has_t1_dependency(self):
        """SC-02 : T3 dépend de T1 → 'T01' dans ses dependencies."""
        tasks = self._gantt_tasks()
        t3 = next(t for t in tasks if t['id'] == 'T03')
        self.assertIn('T01', t3['dependencies'])

    def test_sc02_gantt_t3_has_t2_dependency(self):
        """SC-02 : T3 dépend de T2 → 'T02' dans ses dependencies."""
        tasks = self._gantt_tasks()
        t3 = next(t for t in tasks if t['id'] == 'T03')
        self.assertIn('T02', t3['dependencies'])

    def test_sc02_gantt_t1_no_dependency(self):
        """T1 n'a pas de prédécesseur → dependencies vide."""
        tasks = self._gantt_tasks()
        t1 = next(t for t in tasks if t['id'] == 'T01')
        self.assertEqual(t1['dependencies'], '')

    def test_sc08_retard_task_has_gantt_retard_class(self):
        """SC-08 (Gantt) : T04 en retard → 'gantt-retard' dans custom_class."""
        tasks = self._gantt_tasks()
        t_retard = next(t for t in tasks if t['id'] == 'T04')
        self.assertIn('gantt-retard', t_retard['custom_class'])
        self.assertTrue(t_retard['_en_retard'])

    def test_sc08_terminee_task_no_retard_class(self):
        """Tâche terminée → pas de 'gantt-retard' même si date dépassée."""
        tasks = self._gantt_tasks()
        t1 = next(t for t in tasks if t['id'] == 'T01')
        self.assertNotIn('gantt-retard', t1['custom_class'])

    def test_sc02_gantt_nb_tasks(self):
        tasks = self._gantt_tasks()
        self.assertEqual(len(tasks), 4)


# ─── Tests SC-03 cycle dans formulaire calendrier ─────────────────────────────

class CalendrierCycleFormTests(TestCase):
    """SC-03 : cycle T1↔T2 → erreur explicite dans le formulaire calendrier."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='adm_cycle', password='pass', role='administrateur',
        )
        prov = _make_province('CYC')
        comm = _make_commune(prov, 'Commune CYC')
        plan = PlanAmenagement.objects.create(
            annee=2086, titre='Plan Cycle', budget_total='100000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=cls.admin,
        )
        cls.action = ActionPlan.objects.create(
            plan=plan, commune=comm, type_action='ACT-02',
            description='Cycle', budget_prevu='50000.00',
            priorite=2, statut='programme',
        )

    def test_sc03_cycle_form_returns_200_with_error(self):
        """SC-03 : POSTer un cycle → réponse 200 + message 'cyclique'."""
        c = Client()
        c.login(username='adm_cycle', password='pass')
        url = reverse('plan_action:calendrier_form', kwargs={'action_pk': self.action.pk})
        post_data = {
            'date_debut_prevue': _TODAY.strftime('%Y-%m-%d'),
            'date_fin_prevue': (_TODAY + timedelta(days=20)).strftime('%Y-%m-%d'),
            'mode_realisation': 'regie',
            'chef_projet': str(self.admin.pk),
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Tâche C1
            'form-0-code_tache': 'C01',
            'form-0-nom_tache': 'Cycle T1',
            'form-0-description': '',
            'form-0-date_debut_prevue': _TODAY.strftime('%Y-%m-%d'),
            'form-0-date_fin_prevue': (_TODAY + timedelta(days=10)).strftime('%Y-%m-%d'),
            'form-0-duree_prevue': '10',
            'form-0-responsable': str(self.admin.pk),
            'form-0-type_suivi': 'suivi_travaux',
            'form-0-statut_tache': 'non_demarree',
            # Tâche C2
            'form-1-code_tache': 'C02',
            'form-1-nom_tache': 'Cycle T2',
            'form-1-description': '',
            'form-1-date_debut_prevue': (_TODAY + timedelta(days=10)).strftime('%Y-%m-%d'),
            'form-1-date_fin_prevue': (_TODAY + timedelta(days=20)).strftime('%Y-%m-%d'),
            'form-1-duree_prevue': '10',
            'form-1-responsable': str(self.admin.pk),
            'form-1-type_suivi': 'suivi_travaux',
            'form-1-statut_tache': 'non_demarree',
            # Cycle : C1 dépend de C2 ET C2 dépend de C1
            'anterieures-0': '1',
            'anterieures-1': '0',
        }
        r = c.post(url, post_data)
        # Formulaire re-rendu (pas de redirect) avec message d'erreur
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'cyclique')

    def test_sc03_no_cycle_redirects(self):
        """Sans cycle → redirect vers plan_detail (form valide)."""
        c = Client()
        c.login(username='adm_cycle', password='pass')
        url = reverse('plan_action:calendrier_form', kwargs={'action_pk': self.action.pk})
        post_data = {
            'date_debut_prevue': _TODAY.strftime('%Y-%m-%d'),
            'date_fin_prevue': (_TODAY + timedelta(days=20)).strftime('%Y-%m-%d'),
            'mode_realisation': 'regie',
            'chef_projet': str(self.admin.pk),
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Tâche N1
            'form-0-code_tache': 'N01',
            'form-0-nom_tache': 'No-cycle T1',
            'form-0-description': '',
            'form-0-date_debut_prevue': _TODAY.strftime('%Y-%m-%d'),
            'form-0-date_fin_prevue': (_TODAY + timedelta(days=10)).strftime('%Y-%m-%d'),
            'form-0-duree_prevue': '10',
            'form-0-responsable': str(self.admin.pk),
            'form-0-type_suivi': 'suivi_travaux',
            'form-0-statut_tache': 'non_demarree',
            # Tâche N2 (dépend de N1 — pas de cycle)
            'form-1-code_tache': 'N02',
            'form-1-nom_tache': 'No-cycle T2',
            'form-1-description': '',
            'form-1-date_debut_prevue': (_TODAY + timedelta(days=10)).strftime('%Y-%m-%d'),
            'form-1-date_fin_prevue': (_TODAY + timedelta(days=20)).strftime('%Y-%m-%d'),
            'form-1-duree_prevue': '10',
            'form-1-responsable': str(self.admin.pk),
            'form-1-type_suivi': 'suivi_travaux',
            'form-1-statut_tache': 'non_demarree',
            # N2 dépend de N1 (acyclique)
            'anterieures-1': '0',
        }
        r = c.post(url, post_data)
        self.assertEqual(r.status_code, 302)


# ─── Tests SC-06 et SC-08 dashboard ──────────────────────────────────────────

class SuiviFormTests(TestCase):
    """
    SC-06 : responsable saisit rapport 40 % + photo → visible.
    SC-08 (dashboard) : tâche en retard → en_retard affiché.
    SEC-03 : MIME invalide → rejeté.
    """

    @classmethod
    def setUpTestData(cls):
        cls.operateur = User.objects.create_user(
            username='oper_suivi', password='pass', role='operateur',
        )
        cls.admin = User.objects.create_superuser(
            username='adm_suivi', password='pass', role='administrateur',
        )
        prov = _make_province('SV')
        comm = _make_commune(prov, 'Commune SV')
        plan = PlanAmenagement.objects.create(
            annee=2087, titre='Plan SV', budget_total='100000.00',
            source_financement='budget_etat', statut='en_preparation',
            cree_par=cls.admin,
        )
        action = ActionPlan.objects.create(
            plan=plan, commune=comm, type_action='ACT-03',
            description='SV', budget_prevu='100000.00', priorite=1,
            statut='en_cours',
        )
        cls.cal = CalendrierIntervention.objects.create(
            action=action,
            date_debut_prevue=_TODAY - timedelta(days=20),
            date_fin_prevue=_TODAY + timedelta(days=10),
            mode_realisation='regie',
            chef_projet=cls.operateur,
            statut_calendrier='valide',
        )
        # Tâche dont l'opérateur est responsable (SC-06)
        cls.tache = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='S01', nom_tache='Tâche Suivi',
            date_debut_prevue=_TODAY - timedelta(days=10),
            date_fin_prevue=_TODAY + timedelta(days=10),
            duree_prevue=20, responsable=cls.operateur,
            type_suivi='suivi_travaux', statut_tache='en_cours',
        )
        # Tâche en retard : délai dépassé (SC-08)
        cls.tache_retard = TacheIntervention.objects.create(
            calendrier=cls.cal, code_tache='S02', nom_tache='Tâche Retard',
            date_debut_prevue=_TODAY - timedelta(days=20),
            date_fin_prevue=_TODAY - timedelta(days=3),
            duree_prevue=17, responsable=cls.admin,
            type_suivi='suivi_travaux', statut_tache='non_demarree',
        )

    def setUp(self):
        import tempfile
        self.tmp_media = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def _post_rapport(self, avancement=40, extra=None):
        c = Client()
        c.login(username='oper_suivi', password='pass')
        url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache.pk})
        data = {
            'date_rapport': _TODAY.strftime('%Y-%m-%d'),
            'avancement_pct': avancement,
            'etat_bloc': 'conforme',
            'commentaire': 'Test rapport',
            'type_piece_global': 'photo_chantier',
        }
        if extra:
            data.update(extra)
        return c, c.post(url, data)

    def test_sc06_rapport_saved_with_40_pct(self):
        """SC-06 : rapport 40 % enregistré en base."""
        _, r = self._post_rapport(40)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(
            SuiviAvancement.objects.filter(tache=self.tache, avancement_pct=40).exists()
        )

    def test_sc06_rapport_visible_in_dashboard(self):
        """SC-06 : avancement 40 % apparaît dans suivi_dashboard."""
        SuiviAvancement.objects.create(
            tache=self.tache, auteur=self.operateur,
            date_rapport=_TODAY, avancement_pct=40, etat_bloc='conforme',
        )
        c = Client()
        c.login(username='oper_suivi', password='pass')
        r = c.get(reverse('plan_action:suivi_dashboard', kwargs={'action_pk': self.cal.action.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '40')

    def test_sc06_photo_upload_creates_piece(self):
        """SC-06 : upload photo de chantier → PieceJustificative créée."""
        with self.settings(MEDIA_ROOT=self.tmp_media):
            photo = SimpleUploadedFile('chantier.jpg', _JPEG_BYTES, content_type='image/jpeg')
            c = Client()
            c.login(username='oper_suivi', password='pass')
            url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache.pk})
            r = c.post(url, {
                'date_rapport': _TODAY.strftime('%Y-%m-%d'),
                'avancement_pct': 50,
                'etat_bloc': 'conforme',
                'type_piece_global': 'photo_chantier',
                'fichiers': photo,
            })
            self.assertEqual(r.status_code, 302)
            suivi = SuiviAvancement.objects.filter(tache=self.tache, avancement_pct=50).first()
            self.assertIsNotNone(suivi)
            self.assertTrue(
                PieceJustificative.objects.filter(suivi=suivi, type_piece='photo_chantier').exists()
            )

    def test_sc06_photo_visible_in_historique(self):
        """SC-06 : photo créée → visible dans suivi_historique."""
        suivi = SuiviAvancement.objects.create(
            tache=self.tache, auteur=self.operateur,
            date_rapport=_TODAY, avancement_pct=60, etat_bloc='conforme',
        )
        with self.settings(MEDIA_ROOT=self.tmp_media):
            photo = SimpleUploadedFile('chantier2.jpg', _JPEG_BYTES, content_type='image/jpeg')
            PieceJustificative.objects.create(
                suivi=suivi, type_piece='photo_chantier',
                fichier=photo, libelle='photo2.jpg', uploade_par=self.operateur,
            )
        c = Client()
        c.login(username='oper_suivi', password='pass')
        r = c.get(reverse('plan_action:suivi_historique', kwargs={'tache_pk': self.tache.pk}))
        self.assertEqual(r.status_code, 200)
        # Le template rend libelle via {{ piece.libelle|truncatechars:30 }}
        self.assertContains(r, 'photo2.jpg')

    def test_sec03_invalid_mime_rejected(self):
        """SEC-03 : fichier .exe (MIME invalide) → pas de PieceJustificative."""
        with self.settings(MEDIA_ROOT=self.tmp_media):
            bad_file = SimpleUploadedFile(
                'virus.exe', b'MZ' + b'\x00' * 100,
                content_type='application/x-msdownload',
            )
            c = Client()
            c.login(username='oper_suivi', password='pass')
            url = reverse('plan_action:suivi_form', kwargs={'tache_pk': self.tache.pk})
            nb_before = PieceJustificative.objects.count()
            c.post(url, {
                'date_rapport': _TODAY.strftime('%Y-%m-%d'),
                'avancement_pct': 10,
                'etat_bloc': 'conforme',
                'type_piece_global': 'autre',
                'fichiers': bad_file,
            })
            nb_after = PieceJustificative.objects.count()
            self.assertEqual(nb_before, nb_after)

    def test_sc08_retard_in_dashboard_context(self):
        """SC-08 : tâche_retard (délai dépassé) → badge retard dans dashboard."""
        c = Client()
        c.login(username='oper_suivi', password='pass')
        r = c.get(reverse('plan_action:suivi_dashboard', kwargs={'action_pk': self.cal.action.pk}))
        self.assertEqual(r.status_code, 200)
        # La page doit contenir un indicateur de retard
        self.assertContains(r, 'retard')

    def test_sc08_retard_gantt_class(self):
        """SC-08 : gantt_data de tache_retard contient 'gantt-retard'."""
        c = Client()
        c.login(username='adm_suivi', password='pass')
        r = c.get(reverse('plan_action:gantt_data', kwargs={'action_pk': self.cal.action.pk}))
        self.assertEqual(r.status_code, 200)
        tasks = r.json()['tasks']
        t_retard = next(t for t in tasks if t['id'] == 'S02')
        self.assertIn('gantt-retard', t_retard['custom_class'])
