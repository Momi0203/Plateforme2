"""
Tests carte/ — deux suites :

  RoleRequiredTests        : sécurité des endpoints (SEC-01, SEC-02 — §8.2)
  AcceptanceCriteriaTests  : 15 critères de recette (§12 — CA-01 à CA-15)
"""

import json

from django.contrib.gis.geos import Point, Polygon as GEOSPolygon
from django.test import TestCase
from django.urls import reverse

from compte.models import Utilisateur
from diagnostic.models import (
    EtatSeuil, NATURE_SEGUIA_CHOICES, Perimetre, Seguias, Seuil,
    TronconSeguia,
)


# ── Helpers communs ───────────────────────────────────────────────────────────

def _make_perimetre(**extra):
    """Périmètre minimal valide (tous les FloatField obligatoires renseignés)."""
    defaults = dict(
        nombre_beneficiaires=10, nombre_menages=8,
        superficie_totale=50.0, superficie_agricole_utile=40.0,
        superficie_irriguee=30.0, superficie_en_bour=5.0,
        parcelles_moins_1ha=34.0, parcelles_1_a_3ha=33.0, parcelles_plus_3ha=33.0,
        et0_mm_jour=6.0,
    )
    defaults.update(extra)
    return Perimetre.objects.create(**defaults)


def _make_seuil(nom, perimetre, statut='non_valide', geometrie=None):
    return Seuil.objects.create(
        nom_du_seuil=nom,
        nature_du_seuil='maçonnerie',
        type_du_seuil='déversant',
        materiaux_de_construction='béton',
        debit_mobilise=80.0, longueur=15.0,
        largeur_de_base=4.0, hauteur=1.5,
        largeur_tapis_amortissement=2.0,
        perimetre=perimetre, statut=statut,
        geometrie=geometrie,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Suite 1 — Sécurité rôles (SEC-01, SEC-02)
# ═══════════════════════════════════════════════════════════════════════════════

class RoleRequiredTests(TestCase):
    """Vérifie que role_required bloque les visiteurs (POST) et que
    api_login_required renvoie 403 (pas de redirect) pour les non-authentifiés."""

    @classmethod
    def setUpTestData(cls):
        cls.visiteur  = Utilisateur.objects.create_user(
            username='visiteur_test', password='pass', role='visiteur')
        cls.operateur = Utilisateur.objects.create_user(
            username='oper_test', password='pass', role='operateur')
        cls.editeur   = Utilisateur.objects.create_user(
            username='edit_test', password='pass', role='editeur')

    _BODY_RS = json.dumps({
        'couche': 'provinces', 'champ': 'nom_fr',
        'operateur': 'CONTIENT', 'valeur': 'test',
    })

    def _post(self, url, body='{}'):
        return self.client.post(url, data=body, content_type='application/json')

    # ── Non authentifié → 403 JSON (api_login_required, pas de redirect) ─────

    def test_non_authentifie_post_403(self):
        """Non authentifié + POST → 403 JSON (CA-13 / SEC-01)."""
        resp = self._post(reverse('carte:api_requete_simple'), self._BODY_RS)
        self.assertEqual(resp.status_code, 403)
        self.assertIn('erreur', json.loads(resp.content))

    def test_non_authentifie_get_403(self):
        """Non authentifié + GET → 403 JSON."""
        resp = self.client.get(reverse('carte:api_couches'))
        self.assertEqual(resp.status_code, 403)
        self.assertIn('erreur', json.loads(resp.content))

    # ── Visiteur → 403 sur les endpoints POST ────────────────────────────────

    def test_visiteur_requete_simple_403(self):
        """Visiteur : POST /carte/api/requete/simple/ → 403 (test principal §8.2)."""
        self.client.force_login(self.visiteur)
        resp = self._post(reverse('carte:api_requete_simple'), self._BODY_RS)
        self.assertEqual(resp.status_code, 403)
        data = json.loads(resp.content)
        self.assertIn('erreur', data)

    def test_visiteur_requete_multicritere_403(self):
        self.client.force_login(self.visiteur)
        body = json.dumps({'couche': 'provinces', 'conditions': [
            {'champ': 'nom_fr', 'operateur': '=', 'valeur': 'Errachidia'}
        ], 'logique': 'ET'})
        resp = self._post(reverse('carte:api_requete_multi'), body)
        self.assertEqual(resp.status_code, 403)

    def test_visiteur_outil_buffer_403(self):
        self.client.force_login(self.visiteur)
        resp = self._post(reverse('carte:api_buffer'),
                          json.dumps({'couche': 'seuils', 'distance_m': 500}))
        self.assertEqual(resp.status_code, 403)

    def test_visiteur_export_csv_403(self):
        self.client.force_login(self.visiteur)
        resp = self._post(reverse('carte:api_export_csv'),
                          json.dumps({'couche': 'provinces'}))
        self.assertEqual(resp.status_code, 403)

    def test_visiteur_export_excel_403(self):
        self.client.force_login(self.visiteur)
        resp = self._post(reverse('carte:api_export_excel'),
                          json.dumps({'couche': 'provinces'}))
        self.assertEqual(resp.status_code, 403)

    def test_visiteur_outil_scoring_403(self):
        self.client.force_login(self.visiteur)
        resp = self._post(reverse('carte:api_scoring'),
                          json.dumps({'couche': 'seuils',
                                      'coefficients': {'etat_structurel_digue': 3}}))
        self.assertEqual(resp.status_code, 403)

    # ── Visiteur → 200 sur les endpoints GET (lecture seule) ─────────────────

    def test_visiteur_get_liste_couches_200(self):
        self.client.force_login(self.visiteur)
        self.assertEqual(self.client.get(reverse('carte:api_couches')).status_code, 200)

    def test_visiteur_get_champs_200(self):
        self.client.force_login(self.visiteur)
        self.assertEqual(
            self.client.get(reverse('carte:api_champs', args=['provinces'])).status_code, 200)

    def test_visiteur_get_criteres_scoring_200(self):
        self.client.force_login(self.visiteur)
        self.assertEqual(
            self.client.get(reverse('carte:api_criteres', args=['seuils'])).status_code, 200)

    # ── Opérateur / éditeur → pas de 403 ─────────────────────────────────────

    def test_operateur_requete_simple_200(self):
        self.client.force_login(self.operateur)
        resp = self._post(reverse('carte:api_requete_simple'), self._BODY_RS)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('pks', json.loads(resp.content))

    def test_operateur_export_excel_pas_403(self):
        self.client.force_login(self.operateur)
        resp = self._post(reverse('carte:api_export_excel'),
                          json.dumps({'couche': 'provinces'}))
        self.assertNotEqual(resp.status_code, 403)
        content = b''.join(resp.streaming_content)
        self.assertEqual(content[:4], b'PK\x03\x04')

    def test_editeur_requete_simple_200(self):
        self.client.force_login(self.editeur)
        resp = self._post(reverse('carte:api_requete_simple'), self._BODY_RS)
        self.assertEqual(resp.status_code, 200)

    # ── Qualité de la réponse 403 ─────────────────────────────────────────────

    def test_403_retourne_json(self):
        """Toute réponse 403 de l'API est du JSON avec la clé 'erreur'."""
        self.client.force_login(self.visiteur)
        resp = self._post(reverse('carte:api_requete_simple'), self._BODY_RS)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertIn('erreur', json.loads(resp.content))


# ═══════════════════════════════════════════════════════════════════════════════
# Suite 2 — Critères d'acceptation §12 (CA-01 à CA-15)
# ═══════════════════════════════════════════════════════════════════════════════

class AcceptanceCriteriaTests(TestCase):
    """
    Tests de recette pour les 15 critères d'acceptation (§12).

    CA-03/04/06/07/11 impliquent des interactions JavaScript côté client ;
    on teste ici les endpoints API sous-jacents que ces interactions consomment.
    """

    # ── Fixtures ──────────────────────────────────────────────────────────────

    @classmethod
    def setUpTestData(cls):
        # Utilisateurs
        cls.visiteur  = Utilisateur.objects.create_user(
            username='ca_visiteur', password='pass', role='visiteur')
        cls.operateur = Utilisateur.objects.create_user(
            username='ca_oper', password='pass', role='operateur')

        # Périmètre de base
        cls.perimetre = _make_perimetre()

        # Périmètre avec géométrie polygonale (CA-08 buffer)
        poly = GEOSPolygon(
            ((-5.0, 32.0), (-4.9, 32.0), (-4.9, 32.1), (-5.0, 32.1), (-5.0, 32.0)),
            srid=4326,
        )
        cls.perimetre_geo = _make_perimetre(geometrie=poly)

        # Seuils pour CA-05 (filtre statut)
        cls.s_valide_1 = _make_seuil('S-Valide-1', cls.perimetre, statut='valide',
                                      geometrie=Point(-4.95, 32.05, srid=4326))
        cls.s_valide_2 = _make_seuil('S-Valide-2', cls.perimetre, statut='valide',
                                      geometrie=Point(-4.94, 32.06, srid=4326))
        cls.s_non_valide = _make_seuil('S-NonValide', cls.perimetre, statut='non_valide',
                                        geometrie=Point(-4.93, 32.07, srid=4326))

        # EtatSeuil pour CA-14 (filtre etat_construction_fonctionnement)
        EtatSeuil.objects.create(
            seuil=cls.s_valide_1,
            etat_construction_fonctionnement='mauvais',
        )
        EtatSeuil.objects.create(
            seuil=cls.s_valide_2,
            etat_construction_fonctionnement='t_mauvais',
        )
        EtatSeuil.objects.create(
            seuil=cls.s_non_valide,
            etat_construction_fonctionnement='bon',
        )

        # Séguia + tronçon pour CA-12 et CA-15
        cls.seguia = Seguias.objects.create(
            nom_de_la_seguia='Seg-Test', type_deguia='principale',
            perimetre=cls.perimetre,
        )
        cls.troncon = TronconSeguia.objects.create(
            seguia=cls.seguia, troncon='TR1', forme='trapezoidale',
            longueur=100.0, hauteur_eau=0.3, epaisseur_parois=0.15,
            largeur_meroire=0.5, fruit_de_berge=0.0,
            nature='beton', debit=0.08, type_decoulement='ciel_ouvert',
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _post_op(self, url, body):
        """POST en tant qu'opérateur."""
        self.client.force_login(self.operateur)
        return self.client.post(url, data=body, content_type='application/json')

    def _get_op(self, url):
        """GET en tant qu'opérateur."""
        self.client.force_login(self.operateur)
        return self.client.get(url)

    def _get_vis(self, url):
        """GET en tant que visiteur."""
        self.client.force_login(self.visiteur)
        return self.client.get(url)

    # ── CA-01 : Vue /carte/ avec visiteur ──────────────────────────────────────

    def test_CA01_carte_visiteur_200(self):
        """CA-01 : visiteur → /carte/ → 200 + template index.html rendu."""
        self.client.force_login(self.visiteur)
        resp = self.client.get(reverse('carte:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'carte/index.html')

    def test_CA01_carte_visiteur_contient_groupes(self):
        """CA-01 : le contexte expose les groupes de couches."""
        self.client.force_login(self.visiteur)
        resp = self.client.get(reverse('carte:index'))
        self.assertIn('groupes', resp.context)
        self.assertTrue(len(resp.context['groupes']) > 0)

    # ── CA-02 : Vue /carte/ avec opérateur ────────────────────────────────────

    def test_CA02_carte_operateur_200(self):
        """CA-02 : opérateur → /carte/ → 200."""
        resp = self._get_op(reverse('carte:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'carte/index.html')

    # ── CA-03 : Couche Périmètres accessible via API ──────────────────────────

    def test_CA03_geojson_perimetres_retourne_feature_collection(self):
        """CA-03 (API sous-jacente) : GET /carte/api/couche/perimetres/ → GeoJSON valide."""
        resp = self._get_op(reverse('carte:api_couche', args=['perimetres']))
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertIn('features', data)

    # ── CA-04 : Sélection d'entités via requête ───────────────────────────────

    def test_CA04_requete_simple_retourne_pks(self):
        """CA-04 (API) : requête simple seuils → liste de PKs."""
        body = json.dumps({
            'couche': 'seuils', 'champ': 'statut',
            'operateur': '=', 'valeur': 'valide',
        })
        resp = self._post_op(reverse('carte:api_requete_simple'), body)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('pks', data)
        self.assertIsInstance(data['pks'], list)

    # ── CA-05 : Requête simple seuils statut = valide ─────────────────────────

    def test_CA05_filtre_statut_valide_retourne_uniquement_valides(self):
        """CA-05 : requête seuils statut=valide → seuls les 2 seuils validés."""
        body = json.dumps({
            'couche': 'seuils', 'champ': 'statut',
            'operateur': '=', 'valeur': 'valide',
        })
        resp = self._post_op(reverse('carte:api_requete_simple'), body)
        self.assertEqual(resp.status_code, 200)
        pks = json.loads(resp.content)['pks']

        self.assertIn(self.s_valide_1.pk, pks)
        self.assertIn(self.s_valide_2.pk, pks)
        self.assertNotIn(self.s_non_valide.pk, pks)
        self.assertEqual(len(pks), 2)

    # ── CA-06 : Entité seuil accessible individuellement ─────────────────────

    def test_CA06_geojson_entite_seuil(self):
        """CA-06 (API) : GET /carte/api/couche/seuils/<pk>/ → Feature GeoJSON."""
        resp = self._get_op(
            reverse('carte:api_entite', args=['seuils', self.s_valide_1.pk]))
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertEqual(len(data['features']), 1)
        feat = data['features'][0]
        self.assertEqual(feat['type'], 'Feature')
        self.assertIsNotNone(feat['geometry'])

    # ── CA-07 : Couche provinces listée dans le registre ────────────────────

    def test_CA07_provinces_dans_registre_couches(self):
        """CA-07 (API) : GET /carte/api/couches/ → provinces présente dans la liste."""
        resp = self._get_vis(reverse('carte:api_couches'))
        self.assertEqual(resp.status_code, 200)
        couches = json.loads(resp.content)
        noms = [c['nom'] for c in couches]
        self.assertIn('provinces', noms)

    # ── CA-08 : Outil Buffer ──────────────────────────────────────────────────

    def test_CA08_buffer_retourne_geojson(self):
        """CA-08 : POST buffer sur seuils sélectionnés → FeatureCollection GeoJSON."""
        body = json.dumps({
            'couche': 'seuils',
            'pks': [self.s_valide_1.pk, self.s_valide_2.pk],
            'distance_m': 500,
        })
        resp = self._post_op(reverse('carte:api_buffer'), body)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['type'], 'FeatureCollection')
        # Avec 2 points de sélection, le résultat doit contenir au moins 1 feature
        self.assertGreaterEqual(len(data['features']), 1)
        # La géométrie du tampon doit être en SRID 4326
        geom = data['features'][0]['geometry']
        self.assertIn(geom['type'], ('Polygon', 'MultiPolygon'))

    # ── CA-09 : Export Excel seuils ──────────────────────────────────────────

    def test_CA09_export_excel_seuils_valide(self):
        """CA-09 : export Excel seuils → fichier .xlsx avec colonnes correctes."""
        body = json.dumps({
            'couche': 'seuils',
            'pks': [self.s_valide_1.pk, self.s_valide_2.pk],
        })
        resp = self._post_op(reverse('carte:api_export_excel'), body)
        self.assertEqual(resp.status_code, 200)

        content = b''.join(resp.streaming_content)
        self.assertEqual(content[:4], b'PK\x03\x04', 'Pas un fichier xlsx valide (magic bytes)')

        import io, openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content))
        ws = wb.active
        headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]

        # pk toujours présent + au moins un champ déclaré pour la couche
        self.assertIn('pk', headers)
        self.assertIn('nom_du_seuil', headers)

        # 2 seuils sélectionnés → 2 lignes de données (+ 1 en-tête)
        self.assertEqual(ws.max_row, 3)

    # ── CA-10 : Export carte PDF ─────────────────────────────────────────────

    def test_CA10_export_pdf_retourne_pdf(self):
        """CA-10 : export PDF A3 paysage → fichier avec magic bytes %PDF."""
        body = json.dumps({
            'format': 'A3', 'orientation': 'landscape', 'dpi': 150,
            'map_image': '',           # pas d'image : fond placeholder beige
            'bbox': [-5.5, 31.5, -3.5, 33.5],
            'legende_items': [],
            'elements': {
                'titre': 'Test CA-10', 'legende': True,
                'nord': True, 'echelle': True, 'date': True,
            },
        })
        resp = self._post_op(reverse('carte:api_export_carte'), body)
        self.assertEqual(resp.status_code, 200)
        content = b''.join(resp.streaming_content)
        self.assertEqual(content[:4], b'%PDF', 'Réponse ne commence pas par %PDF')
        self.assertGreater(len(content), 1000)

    # ── CA-11 : Filtre par état général ──────────────────────────────────────

    def test_CA11_filtre_etat_general_mauvais(self):
        """CA-11 (API) : seuils avec etat_construction_fonctionnement=mauvais → PKs corrects."""
        body = json.dumps({
            'couche': 'seuils',
            'champ': 'etat_general',   # champ virtuel via join_etat
            'operateur': '=',
            'valeur': 'mauvais',
        })
        resp = self._post_op(reverse('carte:api_requete_simple'), body)
        self.assertEqual(resp.status_code, 200)
        pks = json.loads(resp.content)['pks']
        self.assertIn(self.s_valide_1.pk, pks)
        self.assertNotIn(self.s_non_valide.pk, pks)

    # ── CA-12 : Évolutivité — nouvelle valeur dans NATURE_SEGUIA_CHOICES ──────

    def test_CA12_nouvelle_valeur_choices_visible_via_api(self):
        """
        CA-12 : ajouter ('pvc', 'PVC') dans NATURE_SEGUIA_CHOICES
        → GET /carte/api/couche/troncons_seguias/champs/nature/valeurs/
          retourne bien la valeur 'pvc' sans modification du JS.

        On patche field.choices directement (point de vérité que l'endpoint interroge)
        ainsi que la liste de module pour être cohérent avec §11.3.
        """
        field = TronconSeguia._meta.get_field('nature')
        original_field_choices = list(field.choices)
        original_module_list   = list(NATURE_SEGUIA_CHOICES)
        try:
            new_choices = original_field_choices + [('pvc', 'PVC')]
            field.choices = new_choices
            NATURE_SEGUIA_CHOICES.append(('pvc', 'PVC'))

            resp = self._get_vis(
                reverse('carte:api_valeurs', args=['troncons_seguias', 'nature']))
            self.assertEqual(resp.status_code, 200)
            valeurs = [v['valeur'] for v in json.loads(resp.content)['valeurs']]
            self.assertIn('pvc', valeurs,
                          'La nouvelle valeur PVC doit apparaître via l\'API sans modifier le JS')
        finally:
            field.choices = original_field_choices
            NATURE_SEGUIA_CHOICES[:] = original_module_list

    # ── Symbologie catégorisée restreinte au résultat d'une requête (?pks=) ──

    def test_valeurs_champ_restreint_par_pks(self):
        """
        Symbologie catégorisée après requête : GET .../etat_general/valeurs/?pks=...
        ne retourne que les valeurs présentes dans le sous-ensemble (entités de la
        requête), pas toutes les valeurs de la couche.
        """
        url = reverse('carte:api_valeurs', args=['seuils', 'etat_general'])
        resp = self._get_op(f'{url}?pks={self.s_valide_1.pk},{self.s_non_valide.pk}')
        self.assertEqual(resp.status_code, 200)
        valeurs = {v['valeur'] for v in json.loads(resp.content)['valeurs']}
        # s_valide_1 = 'mauvais', s_non_valide = 'bon' ; s_valide_2 ('t_mauvais') exclu
        self.assertEqual(valeurs, {'mauvais', 'bon'})
        self.assertNotIn('t_mauvais', valeurs)

    def test_valeurs_champ_sans_pks_toute_la_couche(self):
        """Sans ?pks=, etat_general retourne toutes les valeurs de choices (couche entière)."""
        url = reverse('carte:api_valeurs', args=['seuils', 'etat_general'])
        resp = self._get_op(url)
        self.assertEqual(resp.status_code, 200)
        valeurs = {v['valeur'] for v in json.loads(resp.content)['valeurs']}
        # Le comportement historique expose tout le référentiel de choices
        self.assertIn('t_mauvais', valeurs)
        self.assertIn('bon', valeurs)

    def test_valeurs_champ_pks_invalide_400(self):
        """?pks= non entier → 400 JSON."""
        url = reverse('carte:api_valeurs', args=['seuils', 'etat_general'])
        resp = self._get_op(f'{url}?pks=abc')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('erreur', json.loads(resp.content))

    # ── CA-13 : Accès non authentifié → 403 (pas de redirect) ────────────────

    def test_CA13_acces_non_authentifie_couche_seuils_403(self):
        """CA-13 : GET /carte/api/couche/seuils/ sans connexion → HTTP 403 JSON."""
        # self.client est non-connecté (pas de force_login)
        resp = self.client.get(reverse('carte:api_couche', args=['seuils']))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp['Content-Type'], 'application/json')
        data = json.loads(resp.content)
        self.assertIn('erreur', data)

    def test_CA13_acces_non_authentifie_pas_de_redirect(self):
        """CA-13 (complément) : l'API ne redirige pas, elle renvoie 403."""
        resp = self.client.get(reverse('carte:api_couche', args=['seuils']))
        # Pas de redirect (302/301), seulement un 403 direct
        self.assertNotIn(resp.status_code, [301, 302])
        self.assertEqual(resp.status_code, 403)

    # ── CA-14 : Requête multicritère ─────────────────────────────────────────

    def test_CA14_requete_multicritere_etat_mauvais_ou_t_mauvais(self):
        """CA-14 : multicritère etat_general = 'mauvais' OU 't_mauvais' → 2 seuils."""
        body = json.dumps({
            'couche': 'seuils',
            'conditions': [
                {'champ': 'etat_general', 'operateur': '=', 'valeur': 'mauvais'},
                {'champ': 'etat_general', 'operateur': '=', 'valeur': 't_mauvais'},
            ],
            'logique': 'OU',
        })
        resp = self._post_op(reverse('carte:api_requete_multi'), body)
        self.assertEqual(resp.status_code, 200)
        pks = json.loads(resp.content)['pks']

        self.assertIn(self.s_valide_1.pk, pks,   'seuil avec état mauvais doit être retourné')
        self.assertIn(self.s_valide_2.pk, pks,   'seuil avec état t_mauvais doit être retourné')
        self.assertNotIn(self.s_non_valide.pk, pks, 'seuil état bon ne doit pas apparaître')
        self.assertEqual(len(pks), 2)

    # ── CA-15 : Calcul d'efficience tronçons ──────────────────────────────────

    def test_CA15_efficience_troncons_calcule_et_persiste(self):
        """CA-15 : POST /outils/efficience/ → efficience_calculee et pertes mises à jour."""
        body = json.dumps({'pks': [self.troncon.pk]})
        resp = self._post_op(reverse('carte:api_efficience'), body)
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.content)
        self.assertEqual(data['nb_calcules'], 1)
        self.assertEqual(len(data['erreurs']), 0)

        # Vérifier la persistance en base
        self.troncon.refresh_from_db()
        self.assertIsNotNone(
            self.troncon.efficience_calculee,
            'efficience_calculee doit être renseignée après le calcul',
        )
        self.assertIsNotNone(self.troncon.perte_infiltration_m3s)
        self.assertIsNotNone(self.troncon.perte_vaporisation_m3s)
        self.assertIsNotNone(self.troncon.date_dernier_calcul)

        # L'efficience est dans [0, 100]
        self.assertGreaterEqual(self.troncon.efficience_calculee, 0.0)
        self.assertLessEqual(self.troncon.efficience_calculee, 100.0)

        # Le résultat JSON contient les champs attendus
        r = data['resultats'][0]
        self.assertIn('pk', r)
        self.assertIn('efficience_pourcent', r)
        self.assertIn('perte_infiltration_m3s', r)
        self.assertIn('perte_vaporisation_m3s', r)
