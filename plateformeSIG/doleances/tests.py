"""
Tests unitaires — Doléances & Demandes
Couvre les scénarios SC-01 à SC-10 du CDC.
"""
from django.contrib.messages import get_messages
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from diagnostic.models import Perimetre
from .models import CommentaireRequete, HistoriqueStatut, PieceJointeRequete, Requete

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except Exception:
    User = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user(username, role, email=''):
    return User.objects.create_user(
        username, email or f'{username}@test.ma', 'pass1234!', role=role,
    )


def _perimetre():
    return Perimetre.objects.create(
        ksar_village='Aoufous', commune_territoriale='Aoufous',
        nombre_beneficiaires=120, nombre_menages=80,
        superficie_totale=120.0, superficie_agricole_utile=100.0,
        superficie_irriguee=80.0,
        parcelles_moins_1ha=40.0, parcelles_1_a_3ha=45.0, parcelles_plus_3ha=15.0,
    )


def _requete(emetteur, **kwargs):
    defaults = dict(
        titre='Requête test',
        type_requete='plateforme',
        description='Description test.',
        urgence='normale',
        type_emetteur='agent_ormva',
    )
    defaults.update(kwargs)
    return Requete.objects.create(emetteur=emetteur, **defaults)


def _faux_jpg(nom='photo.jpg', taille=1024):
    return SimpleUploadedFile(nom, b'x' * taille, content_type='image/jpeg')


# ── Base commune ──────────────────────────────────────────────────────────────

class DoleancesBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.visiteur  = _user('visiteur',  'visiteur')
        cls.operateur = _user('operateur', 'operateur', 'op@test.ma')
        cls.editeur   = _user('editeur',   'editeur')
        cls.admin     = _user('admin1',    'administrateur', 'admin@test.ma')
        cls.perimetre = _perimetre()

    def _login(self, user):
        self.client.force_login(user)

    def _msgs(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]


# ── SC-01 ─────────────────────────────────────────────────────────────────────

class SC01VisiteurSoumetPlateforme(DoleancesBase):
    """Un visiteur soumet TYPE_PLATEFORME → statut soumise, référence DD-YYYY-NNNN."""

    def test_creation_requete(self):
        self._login(self.visiteur)
        data = dict(
            titre='Bug affichage carte',
            type_requete='plateforme',
            description='La carte ne charge pas.',
            urgence='normale',
            type_emetteur='agent_ormva',
        )
        resp = self.client.post(reverse('doleances:nouvelle'), data)

        self.assertEqual(Requete.objects.count(), 1)
        req = Requete.objects.first()
        self.assertEqual(req.statut, 'soumise')
        self.assertRegex(req.reference, r'^DD-\d{4}-\d{4}$')
        self.assertRedirects(resp, reverse('doleances:detail', args=[req.pk]))

    def test_confirmation_affichee(self):
        self._login(self.visiteur)
        data = dict(
            titre='Test', type_requete='plateforme',
            description='Desc.', urgence='normale', type_emetteur='agent_ormva',
        )
        resp = self.client.post(reverse('doleances:nouvelle'), data, follow=True)
        self.assertContains(resp, 'DD-')


# ── SC-02 ─────────────────────────────────────────────────────────────────────

class SC02TypePerimetreSansPeriemtre(DoleancesBase):
    """Opérateur soumet TYPE_PERIMETRE sans périmètre → erreur formulaire explicite."""

    def test_rejet_sans_perimetre(self):
        self._login(self.operateur)
        data = dict(
            titre='Rupture canal', type_requete='perimetre',
            description='Brèche importante.', urgence='haute',
            type_emetteur='garde_hydraulique',
            # perimetre absent intentionnellement
        )
        resp = self.client.post(reverse('doleances:nouvelle'), data)

        self.assertEqual(Requete.objects.count(), 0)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp.context['form'], 'perimetre',
            "Le périmètre est obligatoire pour une requête de type 'Requête périmètre agricole'.",
        )

    def test_ok_avec_perimetre(self):
        self._login(self.operateur)
        data = dict(
            titre='Rupture canal', type_requete='perimetre',
            description='Brèche importante.', urgence='haute',
            type_emetteur='garde_hydraulique',
            perimetre=self.perimetre.pk,
        )
        resp = self.client.post(reverse('doleances:nouvelle'), data)
        self.assertEqual(Requete.objects.count(), 1)


# ── SC-03 ─────────────────────────────────────────────────────────────────────

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SC03AdminChangeStatut(DoleancesBase):
    """Admin change statut → HistoriqueStatut créé + email émetteur."""

    def setUp(self):
        self.requete = _requete(self.operateur)

    def test_historique_cree(self):
        self._login(self.admin)
        self.client.post(
            reverse('doleances:changer_statut', args=[self.requete.pk]),
            {'nouveau_statut': 'en_cours', 'commentaire': ''},
        )
        hist = HistoriqueStatut.objects.filter(requete=self.requete)
        self.assertEqual(hist.count(), 1)
        self.assertEqual(hist.first().statut_precedent, 'soumise')
        self.assertEqual(hist.first().statut_nouveau, 'en_cours')

    def test_email_emetteur_envoye(self):
        self._login(self.admin)
        self.client.post(
            reverse('doleances:changer_statut', args=[self.requete.pk]),
            {'nouveau_statut': 'en_cours', 'commentaire': ''},
        )
        self.assertGreater(len(mail.outbox), 0)
        tous = [e for msg in mail.outbox for e in msg.to]
        self.assertIn(self.operateur.email, tous)

    def test_statut_mis_a_jour(self):
        self._login(self.admin)
        self.client.post(
            reverse('doleances:changer_statut', args=[self.requete.pk]),
            {'nouveau_statut': 'en_cours', 'commentaire': ''},
        )
        self.requete.refresh_from_db()
        self.assertEqual(self.requete.statut, 'en_cours')


# ── SC-04 ─────────────────────────────────────────────────────────────────────

class SC04AccesTableauBord(DoleancesBase):
    """Visiteur → 403 ; Opérateur et Admin → 200."""

    def test_visiteur_403(self):
        self._login(self.visiteur)
        resp = self.client.get(reverse('doleances:tableau_de_bord'))
        self.assertEqual(resp.status_code, 403)

    def test_editeur_403(self):
        self._login(self.editeur)
        resp = self.client.get(reverse('doleances:tableau_de_bord'))
        self.assertEqual(resp.status_code, 403)

    def test_operateur_200(self):
        self._login(self.operateur)
        resp = self.client.get(reverse('doleances:tableau_de_bord'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_200(self):
        self._login(self.admin)
        resp = self.client.get(reverse('doleances:tableau_de_bord'))
        self.assertEqual(resp.status_code, 200)

    def test_non_connecte_redirige(self):
        resp = self.client.get(reverse('doleances:tableau_de_bord'))
        self.assertEqual(resp.status_code, 302)


# ── SC-05 ─────────────────────────────────────────────────────────────────────

class SC05ListeFiltree(DoleancesBase):
    """Opérateur ne voit que ses requêtes (émetteur ou assigné)."""

    def setUp(self):
        self.req_mine     = _requete(self.operateur, titre='Ma requête')
        self.req_autre    = _requete(self.visiteur,  titre='Requête visiteur')
        self.req_assignee = _requete(self.visiteur,  titre='Requête assignée')
        self.req_assignee.assignee = self.operateur
        self.req_assignee.save(update_fields=['assignee'])

    def test_voit_siennes_et_assignees(self):
        self._login(self.operateur)
        resp = self.client.get(reverse('doleances:liste'))
        pks = [r.pk for r in resp.context['page_obj'].object_list]
        self.assertIn(self.req_mine.pk,     pks)
        self.assertIn(self.req_assignee.pk, pks)
        self.assertNotIn(self.req_autre.pk, pks)

    def test_visiteur_ne_voit_que_les_siennes(self):
        self._login(self.visiteur)
        resp = self.client.get(reverse('doleances:liste'))
        pks = [r.pk for r in resp.context['page_obj'].object_list]
        self.assertIn(self.req_autre.pk,    pks)
        self.assertNotIn(self.req_mine.pk,  pks)


# ── SC-06 ─────────────────────────────────────────────────────────────────────

class SC06MaxCinqPJ(DoleancesBase):
    """Soumission avec 6 PJ → 5 créées, avertissement sur la 6ᵉ."""

    def test_limite_cinq_pj(self):
        self._login(self.visiteur)
        fichiers = [_faux_jpg(f'img{i}.jpg') for i in range(6)]
        data = dict(
            titre='Test PJ', type_requete='plateforme',
            description='Desc.', urgence='normale',
            type_emetteur='agent_ormva',
            fichiers=fichiers,
        )
        resp = self.client.post(reverse('doleances:nouvelle'), data)

        req = Requete.objects.get()
        self.assertEqual(req.pieces_jointes.count(), 5)
        msgs = self._msgs(resp)
        self.assertTrue(any('Maximum 5' in m for m in msgs))

    def test_cinq_pj_ok(self):
        self._login(self.visiteur)
        fichiers = [_faux_jpg(f'img{i}.jpg') for i in range(5)]
        data = dict(
            titre='Test PJ ok', type_requete='plateforme',
            description='Desc.', urgence='normale',
            type_emetteur='agent_ormva',
            fichiers=fichiers,
        )
        self.client.post(reverse('doleances:nouvelle'), data)
        req = Requete.objects.get()
        self.assertEqual(req.pieces_jointes.count(), 5)


# ── SC-07 ─────────────────────────────────────────────────────────────────────

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SC07EmailCritique(DoleancesBase):
    """Requête urgence critique → email à l'administrateur."""

    def test_email_envoye_critique(self):
        self._login(self.visiteur)
        data = dict(
            titre='Crue imminente', type_requete='plateforme',
            description='Niveau critique.', urgence='critique',
            type_emetteur='garde_hydraulique',
        )
        self.client.post(reverse('doleances:nouvelle'), data)

        tous = [e for msg in mail.outbox for e in msg.to]
        self.assertIn(self.admin.email, tous)
        sujets = [msg.subject for msg in mail.outbox]
        self.assertTrue(any('CRITIQUE' in s.upper() for s in sujets))

    def test_pas_email_urgence_normale(self):
        self._login(self.visiteur)
        data = dict(
            titre='Requête normale', type_requete='plateforme',
            description='Pb mineur.', urgence='normale',
            type_emetteur='agent_ormva',
        )
        self.client.post(reverse('doleances:nouvelle'), data)

        # L'email urgente ne devrait pas être envoyé pour urgence=normale
        emails_urgence = [
            msg for msg in mail.outbox
            if 'CRITIQUE' in msg.subject.upper() or 'HAUTE' in msg.subject.upper()
        ]
        self.assertEqual(len(emails_urgence), 0)

    def test_email_envoye_haute(self):
        self._login(self.visiteur)
        data = dict(
            titre='Brèche haute', type_requete='plateforme',
            description='Brèche.', urgence='haute',
            type_emetteur='garde_hydraulique',
        )
        self.client.post(reverse('doleances:nouvelle'), data)

        tous = [e for msg in mail.outbox for e in msg.to]
        self.assertIn(self.admin.email, tous)


# ── SC-08 ─────────────────────────────────────────────────────────────────────

class SC08ExportCSV(DoleancesBase):
    """Export CSV : admin uniquement."""

    def test_admin_acces_200(self):
        self._login(self.admin)
        resp = self.client.get(reverse('doleances:export_csv'))
        self.assertEqual(resp.status_code, 200)

    def test_visiteur_403(self):
        self._login(self.visiteur)
        resp = self.client.get(reverse('doleances:export_csv'))
        self.assertEqual(resp.status_code, 403)

    def test_operateur_403(self):
        self._login(self.operateur)
        resp = self.client.get(reverse('doleances:export_csv'))
        self.assertEqual(resp.status_code, 403)

    def test_non_connecte_redirige(self):
        resp = self.client.get(reverse('doleances:export_csv'))
        self.assertEqual(resp.status_code, 302)


# ── SC-09 ─────────────────────────────────────────────────────────────────────

class SC09CommentaireSurRequeteFermee(DoleancesBase):
    """Commentaire sur requête clôturée ou rejetée → refusé."""

    def _post_commentaire(self, requete, user):
        self._login(user)
        return self.client.post(
            reverse('doleances:commenter', args=[requete.pk]),
            {'contenu': 'Précision complémentaire'},
        )

    def test_cloturee_refusee(self):
        req = _requete(self.operateur, statut='cloturee')
        resp = self._post_commentaire(req, self.operateur)
        self.assertEqual(CommentaireRequete.objects.count(), 0)
        msgs = self._msgs(resp)
        self.assertTrue(any('clôtur' in m.lower() or 'rejet' in m.lower() for m in msgs))

    def test_rejetee_refusee(self):
        req = _requete(self.operateur, statut='rejetee')
        resp = self._post_commentaire(req, self.operateur)
        self.assertEqual(CommentaireRequete.objects.count(), 0)

    def test_soumise_autorisee(self):
        req = _requete(self.operateur, statut='soumise')
        self._post_commentaire(req, self.operateur)
        self.assertEqual(CommentaireRequete.objects.count(), 1)


# ── SC-10 ─────────────────────────────────────────────────────────────────────

class SC10CleanModelPerimetre(DoleancesBase):
    """TYPE_PERIMETRE sans périmètre → ValidationError au niveau modèle (clean())."""

    def test_full_clean_leve_erreur(self):
        req = Requete(
            titre='Seuil endommagé', type_requete='perimetre',
            description='Brèche.', urgence='haute',
            type_emetteur='garde_hydraulique',
            emetteur=self.operateur,
            # perimetre absent
        )
        with self.assertRaises(ValidationError) as ctx:
            req.full_clean()
        self.assertIn('perimetre', ctx.exception.message_dict)

    def test_full_clean_ok_avec_perimetre(self):
        req = Requete(
            titre='Seuil endommagé', type_requete='perimetre',
            description='Brèche.', urgence='haute',
            type_emetteur='garde_hydraulique',
            emetteur=self.operateur,
            perimetre=self.perimetre,
        )
        req.full_clean()  # ne doit pas lever d'exception

    def test_plateforme_sans_perimetre_ok(self):
        req = Requete(
            titre='Bug', type_requete='plateforme',
            description='Erreur 500.', urgence='normale',
            type_emetteur='agent_ormva',
            emetteur=self.visiteur,
        )
        req.full_clean()  # pas d'erreur sur perimetre pour type plateforme
