from django.urls import path

from . import views, api_views

app_name = "carte"

urlpatterns = [
    # Vue principale
    path("", views.index, name="index"),

    # §7.1 Couches GeoJSON
    path("api/couches/",                           api_views.liste_couches,    name="api_couches"),
    path("api/couches/activables/",                api_views.couches_activables, name="api_couches_activables"),
    path("api/reseau-ouvrage-tete/",               api_views.reseau_ouvrage_tete, name="api_reseau_ouvrage_tete"),
    path("api/couche/<str:nom>/",                  api_views.geojson_couche,   name="api_couche"),
    path("api/couche/<str:nom>/<int:pk>/",         api_views.geojson_entite,   name="api_entite"),
    path("api/couche/<str:nom>/extent/",           api_views.extent_couche,    name="api_extent"),
    path("api/couche/<str:nom>/liste/",            api_views.couche_liste,     name="api_couche_liste"),

    # §7.2 Champs et valeurs
    path("api/couche/<str:nom>/champs/",                       api_views.champs_couche,    name="api_champs"),
    path("api/couche/<str:nom>/champs/<str:champ>/valeurs/",   api_views.valeurs_champ,    name="api_valeurs"),
    path("api/couche/<str:nom>/champs/<str:champ>/stats/",     api_views.stats_champ,      name="api_stats_champ"),
    path("api/couche/<str:nom>/criteres/",                     api_views.criteres_scoring, name="api_criteres"),

    # §7.3 Requêtes
    path("api/requete/simple/",       api_views.requete_simple,       name="api_requete_simple"),
    path("api/requete/multicritere/", api_views.requete_multicritere, name="api_requete_multi"),
    path("api/requete/spatiale/",     api_views.requete_spatiale,     name="api_requete_spatiale"),

    # §7.4 Outils géospatiaux
    path("api/outils/buffer/",        api_views.outil_buffer,       name="api_buffer"),
    path("api/outils/intersection/",  api_views.outil_intersection, name="api_intersection"),
    path("api/outils/union/",         api_views.outil_union,        name="api_union"),
    path("api/outils/dissolve/",      api_views.outil_dissolve,     name="api_dissolve"),
    path("api/outils/near/",          api_views.outil_near,         name="api_near"),
    path("api/outils/stats/",         api_views.outil_stats,        name="api_stats"),
    path("api/outils/efficience/",    api_views.outil_efficience,   name="api_efficience"),
    path("api/outils/manning/",       api_views.outil_manning,      name="api_manning"),
    path("api/outils/scoring/",       api_views.outil_scoring,      name="api_scoring"),

    # Masque hiérarchique (T4/T5)
    path("api/masque/<str:couche_parente>/<int:pk>/<str:couche_enfant>/",
         api_views.masque_enfants, name="api_masque"),

    # §9 FEATURE-C2 — Tableaux enfants ouvrages
    path("api/perimetre/<int:pk>/ouvrages/<str:type_ouvrage>/", api_views.perimetre_ouvrages, name="api_perimetre_ouvrages"),

    # §8 Analyse — Périmètre
    path("api/perimetres/besoin/",               api_views.perimetres_besoin_points, name="api_perimetres_besoin"),
    path("api/perimetres/comparaison-besoin/",   api_views.perimetres_comparaison_besoin, name="api_perimetres_comparaison_besoin"),

    # Box Hydrologie / Crues (Lot 1)
    path("api/bv/crue-points/",                  api_views.bv_crue_points,    name="api_bv_crue_points"),
    path("api/bv/<int:pk>/crue-periodes/",       api_views.bv_crue_periodes,  name="api_bv_crue_periodes"),
    path("api/bv/<int:pk>/tc/",                  api_views.bv_tc,             name="api_bv_tc"),
    path("api/bv/<int:pk>/apports-crue/", api_views.bv_apports_crue, name="api_bv_apports_crue"),

    # Box Bilan eau (Lot 2)
    path("api/perimetres/couverture/",           api_views.perimetres_couverture,    name="api_perimetres_couverture"),
    path("api/perimetre/<int:pk>/bilan-mensuel/", api_views.perimetre_bilan_mensuel, name="api_perimetre_bilan_mensuel"),
    path("api/station-clim/<int:pk>/eto/",       api_views.station_clim_eto,         name="api_station_clim_eto"),

    # Box Efficience réseau (Lot 3)
    path("api/efficiences/liste/",               api_views.efficiences_liste, name="api_efficiences_liste"),
    path("api/seguias/liste/",                   api_views.seguias_liste,     name="api_seguias_liste"),
    path("api/seguia/<int:pk>/profil/",          api_views.seguia_profil,     name="api_seguia_profil"),

    # Box Diagnostic (Lot 4)
    path("api/ouvrages/etat-comparaison/",       api_views.ouvrages_etat_comparaison, name="api_ouvrages_etat_comparaison"),
    path("api/ouvrages/debit-points/",           api_views.ouvrages_debit_points,     name="api_ouvrages_debit_points"),
    path("api/perimetre/<int:pk>/rendement/",    api_views.perimetre_rendement,    name="api_perimetre_rendement"),
    path("api/perimetre/<int:pk>/tours-eau/",    api_views.perimetre_tours_eau,    name="api_perimetre_tours_eau"),
    path("api/perimetre/<int:pk>/volume-bilan/", api_views.perimetre_volume_bilan, name="api_perimetre_volume_bilan"),

    # §8 Analyse — Seuil
    path("api/seuil/<int:pk>/bv/",              api_views.seuil_bv_geojson, name="api_seuil_bv"),
    path("api/seuil/<int:pk>/bv-apport/",       api_views.seuil_bv_apport,  name="api_seuil_bv_apport"),
    path("api/seuil/<int:pk>/apport-crue/",     api_views.seuil_apport_crue, name="api_seuil_apport_crue"),

    # §8 Analyse — Prise locale
    path("api/prise/<int:pk>/bv/",              api_views.prise_bv_geojson, name="api_prise_bv"),
    path("api/prise/<int:pk>/bv-apport/",       api_views.prise_bv_apport,  name="api_prise_bv_apport"),
    path("api/prise/<int:pk>/apport-crue/",     api_views.prise_apport_crue, name="api_prise_apport_crue"),

    # §8 Analyse — Barrage
    path("api/barrage/<int:pk>/bv/",            api_views.barrage_bv_geojson, name="api_barrage_bv"),
    path("api/barrage/<int:pk>/bv-apport/",     api_views.barrage_bv_apport,  name="api_barrage_bv_apport"),
    path("api/barrage/<int:pk>/apport-crue/",   api_views.barrage_apport_crue, name="api_barrage_apport_crue"),

    # §R-IP — Indice de priorité d'intervention
    path("api/outils/indice-priorite/",         api_views.indice_priorite,    name="api_indice_priorite"),

    # §7.5 Exports
    path("api/export/csv/",       api_views.export_csv,       name="api_export_csv"),
    path("api/export/excel/",     api_views.export_excel,     name="api_export_excel"),
    path("api/export/geojson/",   api_views.export_geojson,   name="api_export_geojson"),
    path("api/export/carte/",     api_views.export_carte,     name="api_export_carte"),
    path("api/export/dashboard/", api_views.export_dashboard, name="api_export_dashboard"),
]
