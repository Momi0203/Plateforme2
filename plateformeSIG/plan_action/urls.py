from django.urls import path
from . import views

app_name = 'plan_action'

urlpatterns = [
    # Plans d'aménagement — Axe 1
    path('', views.plan_list, name='plan_list'),
    path('creer/', views.plan_create, name='plan_create'),
    path('<int:pk>/', views.plan_detail, name='plan_detail'),
    path('<int:pk>/modifier/', views.plan_update, name='plan_update'),
    path('<int:pk>/supprimer/', views.plan_delete, name='plan_delete'),

    # Synthèse budgétaire + export Excel + graphes analytiques
    path('<int:pk>/synthese/', views.plan_synthese, name='plan_synthese'),
    path('<int:pk>/synthese/data/', views.synthese_data, name='synthese_data'),
    path('synthese/comparaison/', views.synthese_comparaison, name='synthese_comparaison'),
    path('<int:pk>/export/excel/', views.export_plan_excel, name='export_plan_excel'),

    # Actions du plan
    path('<int:plan_pk>/action/ajouter/', views.action_create, name='action_create'),
    path('action/<int:pk>/modifier/', views.action_update, name='action_update'),
    path('action/<int:pk>/supprimer/', views.action_delete, name='action_delete'),

    # Axe 2 — Calendrier d'intervention
    path('calendriers/', views.calendrier_list, name='calendrier_list'),
    path('action/<int:action_pk>/calendrier/', views.calendrier_form, name='calendrier_form'),
    path('action/<int:action_pk>/valider/', views.valider_calendrier, name='valider_calendrier'),

    # Axe 2 — Gantt (Frappe Gantt)
    path('action/<int:action_pk>/gantt/', views.calendrier_gantt, name='calendrier_gantt'),
    path('action/<int:action_pk>/gantt/data/', views.gantt_data, name='gantt_data'),

    # Axe 2 — PERT (vis.js Network + CPM)
    path('action/<int:action_pk>/pert/', views.calendrier_pert, name='calendrier_pert'),
    path('action/<int:action_pk>/pert/data/', views.pert_data, name='pert_data'),

    # Axe 3 — Suivi d'avancement
    path('action/<int:action_pk>/suivi/', views.suivi_dashboard, name='suivi_dashboard'),
    path('tache/<int:tache_pk>/suivi/', views.suivi_form, name='suivi_form'),
    path('tache/<int:tache_pk>/suivi/liste/', views.suivi_historique, name='suivi_historique'),
    path('piece/<int:piece_pk>/supprimer/', views.piece_delete, name='piece_delete'),

    # Axe 3 — Courbe S (JSON) + Suivi global
    path('action/<int:action_pk>/suivi/courbe/', views.courbe_s_data, name='courbe_s_data'),
    path('suivi/', views.suivi_global, name='suivi_global'),
]
