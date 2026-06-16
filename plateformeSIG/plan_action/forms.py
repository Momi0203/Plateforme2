from django import forms
from django.forms import modelformset_factory
from .models import PlanAmenagement, ActionPlan, CalendrierIntervention, TacheIntervention, SuiviAvancement


W = {'class': 'form-control'}


class PlanAmenagementForm(forms.ModelForm):
    class Meta:
        model = PlanAmenagement
        fields = ['annee', 'titre', 'budget_total', 'source_financement', 'statut', 'description']
        widgets = {
            'annee':              forms.NumberInput(attrs={**W, 'min': 2000, 'max': 2050}),
            'titre':              forms.TextInput(attrs=W),
            'budget_total':       forms.NumberInput(attrs={**W, 'step': '0.01'}),
            'source_financement': forms.Select(attrs=W),
            'statut':             forms.Select(attrs=W),
            'description':        forms.Textarea(attrs={**W, 'rows': 3}),
        }


class ActionPlanForm(forms.ModelForm):
    class Meta:
        model = ActionPlan
        fields = [
            'commune', 'perimetre', 'type_action', 'description',
            'budget_prevu', 'superficie_concernee', 'longueur_prevue',
            'statut', 'priorite', 'observations',
        ]
        widgets = {
            'commune':              forms.Select(attrs=W),
            'perimetre':            forms.Select(attrs=W),
            'type_action':          forms.Select(attrs=W),
            'description':          forms.Textarea(attrs={**W, 'rows': 3}),
            'budget_prevu':         forms.NumberInput(attrs={**W, 'step': '0.01'}),
            'superficie_concernee': forms.NumberInput(attrs={**W, 'step': '0.01'}),
            'longueur_prevue':      forms.NumberInput(attrs={**W, 'step': '0.01'}),
            'statut':               forms.Select(attrs=W),
            'priorite':             forms.Select(attrs=W),
            'observations':         forms.Textarea(attrs={**W, 'rows': 2}),
        }


# ─── Axe 2 — Calendrier ───────────────────────────────────────────────────────

class CalendrierInterventionForm(forms.ModelForm):
    class Meta:
        model = CalendrierIntervention
        fields = ['date_debut_prevue', 'date_fin_prevue', 'mode_realisation', 'chef_projet']
        widgets = {
            'date_debut_prevue': forms.DateInput(attrs={**W, 'type': 'date'}, format='%Y-%m-%d'),
            'date_fin_prevue':   forms.DateInput(attrs={**W, 'type': 'date'}, format='%Y-%m-%d'),
            'mode_realisation':  forms.Select(attrs=W),
            'chef_projet':       forms.Select(attrs=W),
        }


class TacheInterventionForm(forms.ModelForm):
    """Formulaire tâche — taches_anterieures géré manuellement dans la vue."""
    class Meta:
        model = TacheIntervention
        fields = [
            'code_tache', 'nom_tache', 'description',
            'date_debut_prevue', 'date_fin_prevue', 'duree_prevue',
            'responsable', 'type_suivi', 'statut_tache',
        ]
        widgets = {
            'code_tache':        forms.TextInput(attrs={**W, 'placeholder': 'T01'}),
            'nom_tache':         forms.TextInput(attrs=W),
            'description':       forms.Textarea(attrs={**W, 'rows': 2}),
            'date_debut_prevue': forms.DateInput(attrs={**W, 'type': 'date'}, format='%Y-%m-%d'),
            'date_fin_prevue':   forms.DateInput(attrs={**W, 'type': 'date'}, format='%Y-%m-%d'),
            'duree_prevue':      forms.NumberInput(attrs={**W, 'min': 1}),
            'responsable':       forms.Select(attrs=W),
            'type_suivi':        forms.Select(attrs=W),
            'statut_tache':      forms.Select(attrs=W),
        }


TacheFormSet = modelformset_factory(
    TacheIntervention,
    form=TacheInterventionForm,
    extra=1,
    can_delete=True,
)


# ─── Axe 3 — Suivi d'avancement ───────────────────────────────────────────────

class SuiviAvancementForm(forms.ModelForm):
    class Meta:
        model = SuiviAvancement
        fields = ['date_rapport', 'avancement_pct', 'etat_bloc', 'commentaire', 'date_prochaine_echeance']
        widgets = {
            'date_rapport':            forms.DateInput(attrs={**W, 'type': 'date'}),
            'avancement_pct':          forms.NumberInput(attrs={**W, 'min': 0, 'max': 100, 'type': 'number'}),
            'etat_bloc':               forms.Select(attrs=W),
            'commentaire':             forms.Textarea(attrs={**W, 'rows': 3}),
            'date_prochaine_echeance': forms.DateInput(attrs={**W, 'type': 'date'}),
        }
