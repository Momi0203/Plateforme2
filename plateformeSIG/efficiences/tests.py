"""
Tests unitaires des services de calcul d'efficience (T01–T15 de la
spécification, adaptés au modèle de données réel).
"""

import math
import unittest


class _SeguiaStub:
    """Stub minimaliste pour les tests géométriques sans DB."""

    def __init__(self, **kwargs):
        self.forme = 'trapezoidale'
        self.largeur_meroire = None
        self.hauteur_eau = None
        self.fruit_de_berge = 0
        self.diametre = None
        self.longueur = None
        self.debit = None
        self.nature = 'terre'
        self.type_decoulement = 'ciel_ouvert'
        self.efficience_calculee = None
        for k, v in kwargs.items():
            setattr(self, k, v)


class _PerimetreStub:
    def __init__(self, type_de_sol='argileux', et0_mm_jour=None):
        self.type_de_sol = type_de_sol
        self.et0_mm_jour = et0_mm_jour


class TestCoefficients(unittest.TestCase):
    """T01–T02"""

    def test_t01_sol_argileux(self):
        from efficiences.services.coefficients import get_coefficient_c
        c = get_coefficient_c(_PerimetreStub('argileux'), _SeguiaStub(nature='terre'))
        self.assertEqual(c, 12)

    def test_t02_revetement_beton(self):
        from efficiences.services.coefficients import get_coefficient_c
        c = get_coefficient_c(_PerimetreStub('sableux'), _SeguiaStub(nature='beton'))
        self.assertEqual(c, 1)


class TestGeometrie(unittest.TestCase):
    """T03–T04 — b=1.5, h=0.8, z=1, donc largeur_miroir=3.1"""

    def test_t03_perimetre_mouille(self):
        from efficiences.services.infiltration import perimetre_mouille
        s = _SeguiaStub(largeur_meroire=3.1, hauteur_eau=0.8, fruit_de_berge=1)
        attendu = 1.5 + 2 * 0.8 * math.sqrt(2)  # ≈ 3.7627
        self.assertAlmostEqual(perimetre_mouille(s), attendu, places=3)

    def test_t04_section_mouillee(self):
        from efficiences.services.infiltration import section_mouillee
        s = _SeguiaStub(largeur_meroire=3.1, hauteur_eau=0.8, fruit_de_berge=1)
        # S = b*h + z*h² = 1.5*0.8 + 1*0.64 = 1.84
        self.assertAlmostEqual(section_mouillee(s), 1.84, places=3)


class TestVitesse(unittest.TestCase):
    """T05 — Q=0.5, S=1.84, donc V ≈ 0.2717"""

    def test_t05_vitesse(self):
        from efficiences.services.infiltration import calculer_vitesse
        s = _SeguiaStub(largeur_meroire=3.1, hauteur_eau=0.8, fruit_de_berge=1, debit=0.5)
        self.assertAlmostEqual(calculer_vitesse(s), 0.5 / 1.84, places=4)


class TestDalot(unittest.TestCase):
    """T06 — règle dalot : Pv = 0, Pi > 0"""

    def test_t06_dalot(self):
        from efficiences.services.infiltration import perte_infiltration
        from efficiences.services.vaporisation import perte_vaporisation
        s = _SeguiaStub(
            largeur_meroire=3.1, hauteur_eau=0.8, fruit_de_berge=1,
            longueur=100, debit=0.5, type_decoulement='dalot',
        )
        p = _PerimetreStub(et0_mm_jour=5.0)
        self.assertEqual(perte_vaporisation(s, p), 0.0)
        self.assertGreater(perte_infiltration(s, coefficient_c=12), 0.0)


class TestClassification(unittest.TestCase):
    """T07–T09 — classification lue depuis Seguias.type_deguia"""

    class _Seg:
        def __init__(self, t):
            self.type_deguia = t

    def test_t07_principale(self):
        from efficiences.services.efficience_troncon import get_classification
        self.assertEqual(get_classification(self._Seg('principale')), 'principale')

    def test_t08_secondaire(self):
        from efficiences.services.efficience_troncon import get_classification
        self.assertEqual(get_classification(self._Seg('secondaire')), 'secondaire')

    def test_t09_tertiaire(self):
        from efficiences.services.efficience_troncon import get_classification
        self.assertEqual(get_classification(self._Seg('tertiaire')), 'tertiaire')


class TestBornes(unittest.TestCase):
    """T10 — plafonnement de l'efficience entre 0 et 100"""

    def test_t10_efficience_bornee(self):
        # On force des pertes négligeables avec un canal très court →
        # efficience théorique proche de 100% (plafonnée).
        from efficiences.services.efficience_troncon import calculer_efficience_troncon
        s = _SeguiaStub(
            largeur_meroire=3.1, hauteur_eau=0.8, fruit_de_berge=1,
            longueur=0.001, debit=0.5, nature='beton',
        )
        p = _PerimetreStub(et0_mm_jour=0)
        res = calculer_efficience_troncon(s, perimetre=p, persister=False)
        self.assertLessEqual(res['efficience_pourcent'], 100.0)
        self.assertGreaterEqual(res['efficience_pourcent'], 0.0)


class TestAgregation(unittest.TestCase):
    """T11–T13 — moyenne pondérée et cascade"""

    def test_t11_moyenne_ponderee(self):
        # 2 tronçons "principal" (Q>1) : 90% à Q=1.5, 70% à Q=3
        # (90*1.5 + 70*3) / (1.5+3) = (135 + 210) / 4.5 = 76.666...
        from efficiences.services.agregation import efficience_par_categorie
        s1 = _SeguiaStub(debit=1.5, efficience_calculee=90.0, type_deguia='principale')
        s2 = _SeguiaStub(debit=3.0, efficience_calculee=70.0, type_deguia='principale')
        r = efficience_par_categorie([s1, s2])
        self.assertAlmostEqual(r['principale'], (90 * 1.5 + 70 * 3) / 4.5, places=2)
        self.assertIsNone(r['secondaire'])
        self.assertIsNone(r['tertiaire'])

    def test_t12_cascade_complete(self):
        # 90% * 80% * 70% = 50.4%
        from efficiences.services.agregation import efficience_globale_cascade
        e = efficience_globale_cascade({'principale': 90, 'secondaire': 80, 'tertiaire': 70})
        self.assertAlmostEqual(e, 50.4, places=2)

    def test_t13_cascade_categorie_absente(self):
        # 90% * 100%(absente) * 70% = 63%
        from efficiences.services.agregation import efficience_globale_cascade
        e = efficience_globale_cascade({'principale': 90, 'secondaire': None, 'tertiaire': 70})
        self.assertAlmostEqual(e, 63.0, places=2)


class TestPersistanceTroncon(unittest.TestCase):
    """T14 — vérifie que les champs efficience sont écrits sur la séguia
    et que save() est appelé avec update_fields restreint."""

    def test_t14_persistance(self):
        from unittest.mock import MagicMock
        from efficiences.services.efficience_troncon import calculer_efficience_troncon

        s = MagicMock(spec=[
            'forme', 'largeur_meroire', 'hauteur_eau', 'fruit_de_berge', 'diametre',
            'longueur', 'debit', 'nature', 'type_decoulement', 'perimetre',
            'efficience_calculee', 'perte_infiltration_m3s', 'perte_vaporisation_m3s',
            'date_dernier_calcul', 'save',
        ])
        s.forme = 'rectangulaire'
        s.largeur_meroire = 1.0
        s.hauteur_eau = 0.5
        s.fruit_de_berge = 0
        s.diametre = None
        s.longueur = 50
        s.debit = 0.3
        s.nature = 'beton'
        s.type_decoulement = 'ciel_ouvert'

        p = _PerimetreStub(et0_mm_jour=4.5)
        result = calculer_efficience_troncon(s, perimetre=p, persister=True)

        self.assertIsNotNone(s.efficience_calculee)
        self.assertIsNotNone(s.perte_infiltration_m3s)
        self.assertIsNotNone(s.perte_vaporisation_m3s)
        self.assertIsNotNone(s.date_dernier_calcul)

        s.save.assert_called_once_with(update_fields=[
            'efficience_calculee',
            'perte_infiltration_m3s',
            'perte_vaporisation_m3s',
            'date_dernier_calcul',
        ])

        for key in ('coefficient_c', 'perte_infiltration_m3s', 'perte_vaporisation_m3s',
                    'efficience_pourcent', 'classification', 'debit_amont', 'is_dalot'):
            self.assertIn(key, result)


class TestRobustesseValeursManquantes(unittest.TestCase):
    """Robustesse : les services ne plantent pas sur valeurs nulles."""

    def test_debit_nul(self):
        from efficiences.services.efficience_troncon import calculer_efficience_troncon
        s = _SeguiaStub(largeur_meroire=2, hauteur_eau=0.5, fruit_de_berge=1, longueur=10, debit=0)
        p = _PerimetreStub()
        res = calculer_efficience_troncon(s, perimetre=p, persister=False)
        self.assertEqual(res['efficience_pourcent'], 0.0)

    def test_largeur_miroir_nulle(self):
        # Cas dégradé : géométrie partielle, pas de crash
        from efficiences.services.infiltration import perimetre_mouille, section_mouillee
        s = _SeguiaStub(largeur_meroire=None, hauteur_eau=0.5, fruit_de_berge=0)
        self.assertEqual(perimetre_mouille(s), 1.0)  # b=0 + 2*0.5 = 1
        self.assertEqual(section_mouillee(s), 0.0)

    def test_et0_absent(self):
        # ET0 manquant → Pv = 0 sans erreur
        from efficiences.services.vaporisation import perte_vaporisation
        s = _SeguiaStub(longueur=100, largeur_meroire=2, hauteur_eau=0.5, type_decoulement='ciel_ouvert')
        p = _PerimetreStub(et0_mm_jour=None)
        self.assertEqual(perte_vaporisation(s, p), 0.0)

    def test_ouvrage_circulaire_plein(self):
        # Conduite circulaire pleine : P = pi*D, S = pi*D²/4
        import math
        from efficiences.services.infiltration import perimetre_mouille, section_mouillee
        s = _SeguiaStub(forme='circulaire', diametre=1.0, hauteur_eau=1.0)
        self.assertAlmostEqual(perimetre_mouille(s), math.pi, places=4)
        self.assertAlmostEqual(section_mouillee(s), math.pi / 4, places=4)
