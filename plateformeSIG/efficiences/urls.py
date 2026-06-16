from django.urls import path

from . import views

app_name = 'efficiences'

urlpatterns = [
    path('', views.liste_perimetres, name='liste'),
    path('perimetre/<int:perimetre_id>/', views.formulaire_efficience, name='formulaire'),
    path('perimetre/<int:perimetre_id>/calculer/', views.lancer_calcul, name='lancer_calcul'),
    path(
        'perimetre/<int:perimetre_id>/ouvrage/<str:ouvrage_type>/<int:ouvrage_id>/troncons/',
        views.troncons_par_ouvrage,
        name='troncons_par_ouvrage',
    ),
    path(
        'perimetre/<int:perimetre_id>/ouvrage/<str:ouvrage_type>/<int:ouvrage_id>/seguias-disponibles/',
        views.api_seguias_disponibles,
        name='api_seguias_disponibles',
    ),
    path(
        'perimetre/<int:perimetre_id>/enregistrer-liaisons/',
        views.enregistrer_liaisons,
        name='enregistrer_liaisons',
    ),
    path(
        'perimetre/<int:perimetre_id>/carte/',
        views.api_perimetre_carte,
        name='api_perimetre_carte',
    ),
    path('efficience/<int:pk>/valider/', views.valider_efficience, name='valider_efficience'),
    path('efficience/<int:pk>/exporter/excel/', views.exporter_excel_efficience, name='exporter_excel'),
    path('efficience/<int:pk>/exporter/pdf/',   views.exporter_pdf_efficience,   name='exporter_pdf'),
    path('historique/', views.historique, name='historique'),
    path('historique/perimetre/<int:perimetre_id>/', views.historique, name='historique_perimetre'),
]
