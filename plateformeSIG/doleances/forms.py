from django import forms
from .models import Requete, CommentaireRequete, PieceJointeRequete


_fc  = {'class': 'form-control'}
_fcs = {'class': 'form-control form-control-sm'}


class RequeteForm(forms.ModelForm):
    class Meta:
        model  = Requete
        fields = [
            'titre', 'type_requete', 'sous_type', 'description', 'urgence',
            'type_emetteur', 'nom_emetteur', 'contact_emetteur', 'organisation',
            'perimetre', 'ouvrage_type', 'ouvrage_id',
        ]
        widgets = {
            'titre':            forms.TextInput(attrs=_fc),
            'type_requete':     forms.Select(attrs=_fc),
            'sous_type':        forms.Select(attrs=_fc),
            'description':      forms.Textarea(attrs={**_fc, 'rows': 4}),
            'urgence':          forms.Select(attrs=_fc),
            'type_emetteur':    forms.Select(attrs=_fc),
            'nom_emetteur':     forms.TextInput(attrs=_fc),
            'contact_emetteur': forms.TextInput(attrs=_fc),
            'organisation':     forms.TextInput(attrs=_fc),
            'perimetre':        forms.Select(attrs=_fc),
            'ouvrage_type':     forms.Select(attrs=_fc),
            'ouvrage_id':       forms.NumberInput(attrs=_fc),
        }


class CommentaireForm(forms.ModelForm):
    class Meta:
        model   = CommentaireRequete
        fields  = ['contenu', 'interne']
        widgets = {'contenu': forms.Textarea(attrs={**_fc, 'rows': 3})}


class ChangerStatutForm(forms.Form):
    """Formulaire de transition de statut pour le staff."""

    nouveau_statut = forms.ChoiceField(
        label='Nouveau statut',
        widget=forms.Select(attrs=_fc),
    )
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={**_fc, 'rows': 3}),
        required=False,
        label='Commentaire',
    )
    reponse_officielle = forms.CharField(
        widget=forms.Textarea(attrs={**_fc, 'rows': 4}),
        required=False,
        label="Réponse officielle (visible par l'émetteur)",
    )
    assignee = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='— Laisser non assignée —',
        label='Assigner à',
        widget=forms.Select(attrs=_fc),
    )

    def __init__(self, transitions_choices, assignee_queryset=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nouveau_statut'].choices = [('', '— Choisir un statut —')] + list(transitions_choices)
        if assignee_queryset is not None:
            self.fields['assignee'].queryset = assignee_queryset
        else:
            del self.fields['assignee']
