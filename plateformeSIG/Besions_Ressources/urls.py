from django.urls import path
from . import views

app_name = 'besions_ressources'

urlpatterns = [
    # Accueil / liste
    path('', views.bilan_home, name='home'),
    path('coefficients-culturaux/', views.coeff_culture_home, name='coeff_culture_home'),

    # Bilan
    path('bilan/creer/', views.bilan_creer, name='bilan_creer'),
    path('bilan/<int:pk>/', views.bilan_detail, name='bilan_detail'),
    path('bilan/<int:pk>/modifier/', views.bilan_modifier, name='bilan_modifier'),
    path('bilan/<int:pk>/supprimer/', views.bilan_supprimer, name='bilan_supprimer'),
    path('bilan/<int:pk>/calculer/', views.bilan_calculer, name='bilan_calculer'),
    path('bilan/<int:pk>/valider/', views.valider_bilan, name='valider_bilan'),

    # API
    path('api/bilan/<int:pk>/hydrogramme/', views.api_hydrogramme, name='api_hydrogramme'),
    path('api/perimetre/<int:perimetre_id>/info/', views.api_perimetre_info, name='api_perimetre_info'),
    path('api/perimetre/<int:perimetre_id>/ouvrages/', views.api_ouvrages_perimetre, name='api_ouvrages_perimetre'),
    path('api/seuil/<int:seuil_id>/info/', views.api_seuil_info, name='api_seuil_info'),
    path('api/prise/<int:prise_id>/info/', views.api_prise_info, name='api_prise_info'),
    path('api/troncon/<int:troncon_id>/info/', views.api_troncon_info, name='api_troncon_info'),
    path('api/bv/<int:bv_id>/tc/', views.api_bv_tc, name='api_bv_tc'),
    path('api/ouvrage/<str:type_ouvrage>/<int:ouvrage_id>/details/', views.api_ouvrage_details, name='api_ouvrage_details'),

    # Export
    path('bilan/<int:pk>/exporter/excel/', views.bilan_exporter_excel, name='bilan_exporter_excel'),
    path('bilan/<int:pk>/exporter/pdf/',   views.bilan_exporter_pdf,   name='bilan_exporter_pdf'),

    # Stations climatiques
    path('stations/', views.station_list, name='station_list'),
    path('stations/creer/', views.station_creer, name='station_creer'),
    path('stations/<int:pk>/modifier/', views.station_modifier, name='station_modifier'),
    path('stations/<int:pk>/supprimer/', views.station_supprimer, name='station_supprimer'),
    path('stations/insolation-auto/', views.station_insolation_auto, name='station_insolation_auto'),

    # Cultures (référentiel global Kc/Kr — pas de notion de périmètre)
    path('cultures/creer/', views.culture_creer, name='culture_creer'),
    path('cultures/<int:pk>/modifier/', views.culture_modifier, name='culture_modifier'),
    path('cultures/<int:pk>/supprimer/', views.culture_supprimer, name='culture_supprimer'),
]
