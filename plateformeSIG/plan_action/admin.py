from django.contrib import admin
from .models import (
    PlanAmenagement, ActionPlan,
    CalendrierIntervention, TacheIntervention,
    SuiviAvancement, PieceJustificative,
)


class ActionPlanInline(admin.TabularInline):
    model = ActionPlan
    extra = 0
    fields = ('commune', 'type_action', 'priorite', 'budget_prevu', 'statut')
    show_change_link = True


@admin.register(PlanAmenagement)
class PlanAmenagementAdmin(admin.ModelAdmin):
    list_display = ('annee', 'titre', 'budget_total', 'source_financement', 'statut', 'taux_realisation', 'cree_par')
    list_filter = ('statut', 'source_financement', 'annee')
    search_fields = ('titre', 'description')
    readonly_fields = ('date_creation', 'taux_realisation')
    inlines = [ActionPlanInline]
    ordering = ('-annee',)


@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ('plan', 'commune', 'type_action', 'priorite', 'budget_prevu', 'statut')
    list_filter = ('statut', 'type_action', 'priorite', 'plan__annee')
    search_fields = ('description', 'observations', 'commune__nom')
    ordering = ('plan', 'priorite')


class TacheInterventionInline(admin.TabularInline):
    model = TacheIntervention
    extra = 0
    fields = ('code_tache', 'nom_tache', 'date_debut_prevue', 'date_fin_prevue', 'duree_prevue', 'responsable', 'statut_tache')
    show_change_link = True


@admin.register(CalendrierIntervention)
class CalendrierInterventionAdmin(admin.ModelAdmin):
    list_display = ('action', 'date_debut_prevue', 'date_fin_prevue', 'mode_realisation', 'chef_projet', 'statut_calendrier')
    list_filter = ('statut_calendrier', 'mode_realisation')
    readonly_fields = ('date_validation', 'valide_par')
    inlines = [TacheInterventionInline]


@admin.register(TacheIntervention)
class TacheInterventionAdmin(admin.ModelAdmin):
    list_display = ('code_tache', 'nom_tache', 'calendrier', 'responsable', 'statut_tache', 'date_debut_prevue', 'date_fin_prevue')
    list_filter = ('statut_tache', 'type_suivi')
    search_fields = ('code_tache', 'nom_tache')
    filter_horizontal = ('taches_anterieures',)


class PieceJustificativeInline(admin.TabularInline):
    model = PieceJustificative
    extra = 0
    fields = ('type_piece', 'libelle', 'fichier', 'date_document')
    readonly_fields = ('date_upload',)


@admin.register(SuiviAvancement)
class SuiviAvancementAdmin(admin.ModelAdmin):
    list_display = ('tache', 'auteur', 'date_rapport', 'avancement_pct', 'etat_bloc')
    list_filter = ('etat_bloc', 'date_rapport')
    readonly_fields = ('date_saisie',)
    inlines = [PieceJustificativeInline]


@admin.register(PieceJustificative)
class PieceJustificativeAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'type_piece', 'suivi', 'uploade_par', 'date_upload')
    list_filter = ('type_piece',)
    readonly_fields = ('date_upload',)
