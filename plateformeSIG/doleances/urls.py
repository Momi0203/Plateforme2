from django.urls import path
from . import views

app_name = 'doleances'

urlpatterns = [
    path('',                    views.liste,           name='liste'),
    path('nouvelle/',           views.nouvelle,        name='nouvelle'),
    path('<int:pk>/',           views.detail,          name='detail'),
    path('<int:pk>/statut/',    views.changer_statut,  name='changer_statut'),
    path('<int:pk>/commenter/', views.commenter,       name='commenter'),
    path('tableau-de-bord/',    views.tableau_de_bord, name='tableau_de_bord'),
    path('export-csv/',         views.export_csv,      name='export_csv'),
    path('carte/',              views.carte_requetes,  name='carte_requetes'),
]
