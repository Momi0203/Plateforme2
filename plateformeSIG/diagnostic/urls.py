from django.urls import path
from . import views

app_name = 'diagnostic'

urlpatterns = [
    # Accueil
    path('', views.accueil_diagnostic, name='accueil_diagnostic'),

    # Import unifié SHP — wizard 2 étapes
    path('importer-shp/', views.shp_import_unified, name='shp_import_unified'),
    path('importer-shp/mapping/', views.shp_import_mapping, name='shp_import_mapping'),

    # Exports Excel
    path('export-enquete/', views.export_enquete_global, name='export_enquete_global'),
    path('perimetres/<int:pk>/export-excel/', views.perimetre_export_excel, name='perimetre_export_excel'),

    # Suivi et évaluation — hub + pages par type
    path('suivi/', views.suivi_evaluation, name='suivi_evaluation'),
    path('suivi/seuils/', views.suivi_seuils, name='suivi_seuils'),
    path('suivi/barrages/', views.suivi_barrages, name='suivi_barrages'),
    path('suivi/khettaras/', views.suivi_khettaras, name='suivi_khettaras'),
    path('suivi/forages/', views.suivi_forages, name='suivi_forages'),
    path('suivi/prises/', views.suivi_prises, name='suivi_prises'),
    path('suivi/seguias/', views.suivi_seguias, name='suivi_seguias'),
    path('suivi/murs/', views.suivi_murs, name='suivi_murs'),

    # API cascade Province → Communes
    path('api/communes/', views.communes_par_province, name='api_communes'),

    # Périmètres
    path('perimetres/', views.perimetre_list, name='perimetre_list'),
    path('perimetres/ajouter/', views.perimetre_create, name='perimetre_create'),
    path('perimetres/<int:pk>/modifier/', views.perimetre_edit, name='perimetre_edit'),
    path('perimetres/<int:pk>/valider/', views.perimetre_valider, name='perimetre_valider'),
    path('perimetres/<int:pk>/supprimer/', views.perimetre_delete, name='perimetre_delete'),
    path('perimetres/importer-shp/', views.perimetre_shp_import, name='perimetre_shp_import'),

    # Ouvrages de tête — détail périmètre
    path('ouvrages-tete/<int:pk>/', views.ouvrages_tete_detail, name='ouvrages_tete_detail'),

    # Seuils
    path('ouvrages-tete/<int:perimetre_pk>/seuil/ajouter/', views.seuil_create, name='seuil_create'),
    path('seuil/<int:pk>/modifier/', views.seuil_edit, name='seuil_edit'),
    path('seuil/<int:pk>/diagnostic/', views.seuil_diagnostic, name='seuil_diagnostic'),
    path('seuil/<int:pk>/valider/', views.seuil_valider, name='seuil_valider'),
    path('seuil/<int:pk>/supprimer/', views.seuil_delete, name='seuil_delete'),
    path('seuils/importer-shp/', views.seuil_shp_import, name='seuil_shp_import'),

    # Murs de protection
    path('ouvrages-tete/<int:perimetre_pk>/mur/ajouter/', views.mur_create, name='mur_create'),
    path('mur/<int:pk>/modifier/', views.mur_edit, name='mur_edit'),
    path('mur/<int:pk>/diagnostic/', views.mur_diagnostic, name='mur_diagnostic'),
    path('mur/<int:pk>/valider/', views.mur_valider, name='mur_valider'),
    path('mur/<int:pk>/supprimer/', views.mur_delete, name='mur_delete'),
    path('murs/importer-shp/', views.mur_shp_import, name='mur_shp_import'),

    # Barrages de retenue
    path('ouvrages-tete/<int:perimetre_pk>/barrage/ajouter/', views.barrage_create, name='barrage_create'),
    path('barrage/<int:pk>/modifier/', views.barrage_edit, name='barrage_edit'),
    path('barrage/<int:pk>/diagnostic/', views.barrage_diagnostic, name='barrage_diagnostic'),
    path('barrage/<int:pk>/valider/', views.barrage_valider, name='barrage_valider'),
    path('barrage/<int:pk>/supprimer/', views.barrage_delete, name='barrage_delete'),
    path('barrages/importer-shp/', views.barrage_shp_import, name='barrage_shp_import'),

    # Khettaras
    path('ouvrages-tete/<int:perimetre_pk>/khettara/ajouter/', views.khettara_create, name='khettara_create'),
    path('khettara/<int:pk>/modifier/', views.khettara_edit, name='khettara_edit'),
    path('khettara/<int:pk>/diagnostic/', views.khettara_diagnostic, name='khettara_diagnostic'),
    path('khettara/<int:pk>/valider/', views.khettara_valider, name='khettara_valider'),
    path('khettara/<int:pk>/supprimer/', views.khettara_delete, name='khettara_delete'),
    path('khettaras/importer-shp/', views.khettara_shp_import, name='khettara_shp_import'),

    # Forages / Puits
    path('ouvrages-tete/<int:perimetre_pk>/forage/ajouter/', views.forage_create, name='forage_create'),
    path('forage/<int:pk>/modifier/', views.forage_edit, name='forage_edit'),
    path('forage/<int:pk>/diagnostic/', views.forage_diagnostic, name='forage_diagnostic'),
    path('forage/<int:pk>/valider/', views.forage_valider, name='forage_valider'),
    path('forage/<int:pk>/supprimer/', views.forage_delete, name='forage_delete'),
    path('forages/importer-shp/', views.forage_shp_import, name='forage_shp_import'),

    # Prises locales
    path('ouvrages-tete/<int:perimetre_pk>/prise/ajouter/', views.prise_create, name='prise_create'),
    path('prise/<int:pk>/modifier/', views.prise_edit, name='prise_edit'),
    path('prise/<int:pk>/diagnostic/', views.prise_diagnostic, name='prise_diagnostic'),
    path('prise/<int:pk>/valider/', views.prise_valider, name='prise_valider'),
    path('prise/<int:pk>/supprimer/', views.prise_delete, name='prise_delete'),
    path('prises/importer-shp/', views.prise_shp_import, name='prise_shp_import'),

    # Réseaux d'irrigation — détail périmètre
    path('reseaux-irrigation/<int:pk>/', views.reseaux_irrigation_detail, name='reseaux_irrigation_detail'),

    # Séguias (identité)
    path('reseaux-irrigation/<int:perimetre_pk>/seguia/ajouter/', views.seguia_create, name='seguia_create'),
    path('seguia/<int:pk>/modifier/', views.seguia_edit, name='seguia_edit'),
    path('seguia/<int:pk>/valider/', views.seguia_valider, name='seguia_valider'),
    path('seguia/<int:pk>/supprimer/', views.seguia_delete, name='seguia_delete'),
    path('seguias/importer-shp/', views.seguia_shp_import, name='seguia_shp_import'),

    # Tronçons de séguia (dimensions + diagnostic + validation)
    path('seguia/<int:seguia_pk>/troncon/ajouter/', views.troncon_create, name='troncon_create'),
    path('troncon/<int:pk>/modifier/', views.troncon_edit, name='troncon_edit'),
    path('troncon/<int:pk>/supprimer/', views.troncon_delete, name='troncon_delete'),
    path('troncon/<int:pk>/valider/', views.troncon_valider, name='troncon_valider'),
    path('troncon/<int:pk>/diagnostic/', views.troncon_diagnostic, name='troncon_diagnostic'),
]
