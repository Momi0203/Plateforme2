from django.urls import path
from . import views

urlpatterns = [
    path('', views.accueil, name='accueil_hydro'),

    # SHP upload (AJAX)
    path('upload-shp/', views.upload_shp, name='upload_shp'),
    path('bassins/import-multiple/', views.importer_bv_multiple, name='importer_bv_multiple'),

    # Bassin Versant
    path('bassins/', views.liste_bv, name='liste_bv'),
    path('bassins/nouveau/', views.creer_bv, name='creer_bv'),
    path('bassins/<int:pk>/', views.detail_bv, name='detail_bv'),
    path('bassins/<int:pk>/reseau.geojson', views.bv_reseau_geojson, name='bv_reseau_geojson'),
    path('bassins/<int:pk>/modifier/', views.modifier_bv, name='modifier_bv'),
    path('bassins/<int:pk>/supprimer/', views.supprimer_bv, name='supprimer_bv'),
    path('bassins/supprimer-multiple/', views.supprimer_bv_multiple, name='supprimer_bv_multiple'),

    # Station Pluviométrique
    path('stations-pluvio/', views.liste_stations_pluvio, name='liste_stations_pluvio'),
    path('stations-pluvio/nouvelle/', views.creer_station_pluvio, name='creer_station_pluvio'),
    path('stations-pluvio/<int:pk>/', views.detail_station_pluvio, name='detail_station_pluvio'),
    path('stations-pluvio/<int:pk>/modifier/', views.modifier_station_pluvio, name='modifier_station_pluvio'),
    path('stations-pluvio/<int:pk>/supprimer/', views.supprimer_station_pluvio, name='supprimer_station_pluvio'),

    # Station Hydrométrique
    path('stations-hydro/', views.liste_stations_hydro, name='liste_stations_hydro'),
    path('stations-hydro/nouvelle/', views.creer_station_hydro, name='creer_station_hydro'),
    path('stations-hydro/<int:pk>/', views.detail_station_hydro, name='detail_station_hydro'),
    path('stations-hydro/<int:pk>/modifier/', views.modifier_station_hydro, name='modifier_station_hydro'),
    path('stations-hydro/<int:pk>/supprimer/', views.supprimer_station_hydro, name='supprimer_station_hydro'),

    # Coefficients Montana
    path('montana/', views.liste_coefficients, name='liste_coefficients'),
    path('montana/nouveau/', views.creer_coefficient, name='creer_coefficient'),
    path('montana/<int:pk>/modifier/', views.modifier_coefficient, name='modifier_coefficient'),
    path('montana/<int:pk>/supprimer/', views.supprimer_coefficient, name='supprimer_coefficient'),

    # Analyses
    path('analyses/', views.liste_analyses, name='liste_analyses'),
    path('analyses/lancer/<int:bv_id>/', views.lancer_analyse, name='lancer_analyse'),
    path('analyses/<int:pk>/resultat/', views.resultat_analyse, name='resultat_analyse'),
    path('analyses/<int:pk>/supprimer/', views.supprimer_analyse, name='supprimer_analyse'),
    path('analyses/<int:pk>/annotations/', views.sauvegarder_annotations, name='sauvegarder_annotations'),
    path('analyses/<int:pk>/recalculer/', views.recalculer_analyse, name='recalculer_analyse'),
    path('analyses/<int:pk>/valider/', views.valider_analyse, name='valider_analyse'),
    path('analyses/<int:pk>/export/excel/', views.exporter_excel, name='exporter_excel'),
    path('analyses/<int:pk>/export/pdf/',   views.exporter_pdf,   name='exporter_pdf'),
]
